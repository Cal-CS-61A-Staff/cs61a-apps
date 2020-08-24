import json
import os
import shutil
from time import sleep
from typing import List
from urllib.parse import urlparse

import requests
import sqlalchemy
import sqlalchemy.engine.url

from build import gen_working_dir
from app_config import App, WEB_DEPLOY_TYPES
from common.db import connect_db
from common.rpc.auth import post_slack_message
from common.rpc.secrets import create_master_secret, get_secret
from shell_utils import sh, tmp_directory


DB_INSTANCE_NAME = "cs61a-140900:us-west2:cs61a-apps"


def gen_env_variables(app: App, pr_number: int):
    database_url = sqlalchemy.engine.url.URL(
        drivername="mysql+pymysql",
        username="root",
        password=get_secret(secret_name="ROOT_DATABASE_PW"),
        database=app.name,
        query={"unix_socket": "{}/{}".format("/cloudsql", DB_INSTANCE_NAME)},
    ).__to_string__(hide_password=False)

    public_value, staging_value = create_master_secret(created_app_name=app.name)

    master_secret = public_value if pr_number == 0 else staging_value

    return dict(
        ENV="prod",
        DATABASE_URL=database_url,
        INSTANCE_CONNECTION_NAME=DB_INSTANCE_NAME,
        APP_MASTER_SECRET=master_secret,
    )


def gen_url(app_name: str, pr_number: int):
    if pr_number == 0:
        return f"{app_name}.experiments.cs61a.org/*"
    else:
        return f"{pr_number}.pr.{app_name}.experiments.cs61a.org/*"


def gen_service_name(app_name: str, pr_number: int):
    if pr_number == 0:
        return app_name
    else:
        return f"{app_name}-pr{pr_number}"


def deploy_commit(app: App, pr_number: int):
    with tmp_directory():
        os.chdir(gen_working_dir(app))
        {
            "flask": run_flask_deploy,
            "docker": run_dockerfile_deploy,
            "none": run_noop_deploy,
        }[app.config["deploy_type"]](app, pr_number)


def run_flask_deploy(app: App, pr_number: int):
    shutil.copy("../../dockerfiles/flask.Dockerfile", "./Dockerfile")
    run_dockerfile_deploy(app, pr_number)


def run_dockerfile_deploy(app: App, pr_number: int):
    for f in os.listdir("../../deploy_files"):
        shutil.copyfile(f"../../deploy_files/{f}", f"./{f}")
    service_name = gen_service_name(app.name, pr_number)
    sh(
        "gcloud",
        "builds",
        "submit",
        "-q",
        "--tag",
        f"gcr.io/cs61a-140900/{service_name}",
    )
    sh(
        "gcloud",
        "run",
        "deploy",
        service_name,
        "--image",
        f"gcr.io/cs61a-140900/{service_name}",
        "--region",
        "us-west1",
        "--platform",
        "managed",
        "--timeout",
        "15m",
        "--memory",
        app.config["memory_limit"],
        "--concurrency",
        str(app.config["concurrency"]),
        "--allow-unauthenticated",
        "--add-cloudsql-instances",
        DB_INSTANCE_NAME,
        "--update-env-vars",
        ",".join(
            f"{key}={val}" for key, val in gen_env_variables(app, pr_number).items()
        ),
        "-q",
    )
    if pr_number == 0:
        domains = json.loads(
            sh(
                "gcloud",
                "beta",
                "run",
                "domain-mappings",
                "list",
                "--platform",
                "managed",
                "--region",
                "us-west1",
                "--format",
                "json",
                capture_output=True,
            )
        )
        for domain in app.config["first_party_domains"]:
            for domain_config in domains:
                if domain_config["metadata"]["name"] == domain:
                    break
            else:
                sh(
                    "gcloud",
                    "beta",
                    "run",
                    "domain-mappings",
                    "create",
                    "--service",
                    service_name,
                    "--domain",
                    domain,
                    "--platform",
                    "managed",
                    "--region",
                    "us-west1",
                )


def run_noop_deploy(_app: App, _pr_number: int):
    pass


def delete_unused_services(pr_number: int = None):
    services = json.loads(
        sh(
            "gcloud",
            "run",
            "services",
            "list",
            "--platform",
            "managed",
            "--region",
            "us-west1",
            "--format",
            "json",
            "-q",
            capture_output=True,
        )
    )
    with connect_db() as db:
        if pr_number is None:
            active_services = db("SELECT app, pr_number FROM services", []).fetchall()
        else:
            active_services = db(
                "SELECT app, pr_number FROM services WHERE pr_number != %s", [pr_number]
            ).fetchall()

    active_service_names = set(
        gen_service_name(app, pr_number) for app, pr_number in active_services
    )

    for service in services:
        if service["metadata"]["name"] not in active_service_names:
            if pr_number is None:
                post_slack_message(
                    course="cs61a",
                    message=f"<!channel> Service f{service['metadata']['name']} was not detected in master, and the "
                    "buildserver attepted to delete it. For safety reasons, the buildserver will not delete "
                    "a production service. Please visit the Cloud Run console and shut the service down "
                    "manually, or review the most recent push to master if you believe that something has "
                    "gone wrong.",
                    purpose="infra",
                )
            else:
                sh(
                    "gcloud",
                    "run",
                    "services",
                    "delete",
                    service["metadata"]["name"],
                    "--platform",
                    "managed",
                    "--region",
                    "us-west1",
                    "-q",
                )

    if pr_number is not None:
        with connect_db() as db:
            db("DELETE FROM services WHERE pr_number=%s", [pr_number])


def update_service_routes(apps: List[App], pr_number: int):
    if pr_number == 0:
        return  # no updates needed for deploys to master

    services = json.loads(
        sh(
            "gcloud",
            "run",
            "services",
            "list",
            "--platform",
            "managed",
            "--format",
            "json",
            capture_output=True,
        )
    )
    for app in apps:
        if app.config["deploy_type"] not in WEB_DEPLOY_TYPES:
            continue
        for service in services:
            if service["metadata"]["name"] == gen_service_name(app.name, pr_number):
                hostname = urlparse(service["status"]["address"]["url"]).netloc
                for _ in range(2):
                    try:
                        requests.post(
                            "https://pr.cs61a.org/create_subdomain",
                            json=dict(
                                app=app.name,
                                pr_number=pr_number,
                                pr_host=hostname,
                                secret=get_secret(secret_name="PR_WEBHOOK_SECRET"),
                            ),
                        )
                    except requests.exceptions.ConnectionError:
                        # pr_proxy will throw when nginx restarts, but that's just expected
                        sleep(5)  # let nginx restart
                break
        else:
            assert False

import json
import os
import shutil
from subprocess import CalledProcessError
from time import sleep
from typing import List
from urllib.parse import urlparse

import requests
import sqlalchemy
import sqlalchemy.engine.url

from build import gen_working_dir
from app_config import App, CLOUD_RUN_DEPLOY_TYPES, WEB_DEPLOY_TYPES
from common.db import connect_db
from common.rpc.auth import post_slack_message
from common.rpc.secrets import create_master_secret, get_secret, load_all_secrets
from common.shell_utils import sh, tmp_directory
from pypi_utils import update_setup_py

DB_INSTANCE_NAME = "cs61a-140900:us-west2:cs61a-apps-us-west1"


def gen_env_variables(app: App, pr_number: int):
    database_url = sqlalchemy.engine.url.URL(
        drivername="mysql+pymysql",
        username="root",
        password=get_secret(secret_name="ROOT_DATABASE_PW"),
        database=app.name.replace("-", "_"),
        query={"unix_socket": "{}/{}".format("/cloudsql", DB_INSTANCE_NAME)},
    ).__to_string__(hide_password=False)

    public_value, staging_value = create_master_secret(created_app_name=app.name)

    master_secret = public_value if pr_number == 0 else staging_value

    return dict(
        ENV="prod",
        DATABASE_URL=database_url,
        INSTANCE_CONNECTION_NAME=DB_INSTANCE_NAME,
        APP_MASTER_SECRET=master_secret,
        **(load_all_secrets(created_app_name=app.name) if pr_number == 0 else {}),
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
            "pypi": run_pypi_deploy,
            "cloud_function": run_cloud_function_deploy,
            "static": run_static_deploy,
            "none": run_noop_deploy,
        }[app.config["deploy_type"]](app, pr_number)


def run_flask_deploy(app: App, pr_number: int):
    shutil.copy("../../dockerfiles/flask.Dockerfile", "./Dockerfile")
    run_dockerfile_deploy(app, pr_number)


def run_dockerfile_deploy(app: App, pr_number: int):
    for f in os.listdir("../../deploy_files"):
        shutil.copyfile(f"../../deploy_files/{f}", f"./{f}")
    service_name = gen_service_name(app.name, pr_number)
    prod_service_name = gen_service_name(app.name, 0)
    with open("cloudbuild.yaml", "a+") as f:
        f.seek(0)
        contents = f.read()
        contents = contents.replace("SERVICE_NAME", service_name)
        contents = contents.replace("PROD_SERVICE_NAME", prod_service_name)
        f.seek(0)
        f.truncate()
        f.write(contents)
    sh("gcloud", "builds", "submit", "-q", "--config", "cloudbuild.yaml")
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
        jobs = json.loads(
            sh(
                "gcloud",
                "scheduler",
                "jobs",
                "list",
                "-q",
                "--format=json",
                capture_output=True,
            )
        )
        for job in jobs:
            name = job["name"].split("/")[-1]
            if name.startswith(f"{app}-"):
                sh("gcloud", "scheduler", "jobs", "delete", name, "-q")

        for job in app.config["tasks"]:
            sh(
                "gcloud",
                "beta",
                "scheduler",
                "jobs",
                "create",
                "http",
                f"{app}-{job['name']}",
                f"--schedule={job['schedule']}",
                f"--uri=https://{app}.cs61a.org/jobs/{job['name']}",
                "--attempt-deadline=1200s",
                "-q",
            )


def run_pypi_deploy(app: App, pr_number: int):
    sh("python", "-m", "venv", "env")
    update_setup_py(app, pr_number)
    sh("env/bin/pip", "install", "setuptools")
    sh("env/bin/pip", "install", "wheel")
    sh("env/bin/python", "setup.py", "sdist", "bdist_wheel")
    sh(
        "twine",
        "upload",
        *(f"dist/{file}" for file in os.listdir("dist")),
        env=dict(
            TWINE_USERNAME="__token__",
            TWINE_PASSWORD=get_secret(secret_name="PYPI_PASSWORD"),
        ),
    )


def run_cloud_function_deploy(app: App, pr_number: int):
    if pr_number != 0:
        return
    sh(
        "gcloud",
        "functions",
        "deploy",
        app.name,
        "--runtime",
        "python37",
        "--trigger-http",
        "--entry-point",
        "index",
        "--timeout",
        "500",
    )


def run_static_deploy(app: App, pr_number: int):
    bucket = f"gs://{gen_service_name(app.name, pr_number)}.buckets.cs61a.org"
    try:
        sh("gsutil", "mb", "-b", "on", bucket)
    except CalledProcessError:
        # bucket already exists
        pass
    sh("gsutil", "-m", "rsync", "-dR", ".", bucket)


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
            if "pr" not in service["metadata"]["name"]:
                post_slack_message(
                    course="cs61a",
                    message=f"<!channel> Service `{service['metadata']['name']}` was not detected in master, and the "
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

        def get_hostname(service_name):
            for service in services:
                if service["metadata"]["name"] == service_name:
                    return urlparse(service["status"]["address"]["url"]).netloc
            return None

        if app.config["deploy_type"] not in WEB_DEPLOY_TYPES:
            continue
        if app.config["deploy_type"] in CLOUD_RUN_DEPLOY_TYPES:
            hostname = get_hostname(gen_service_name(app.name, pr_number))
            assert hostname is not None
            create_subdomain(app.name, pr_number, hostname)
        elif app.config["deploy_type"] == "static":
            for consumer in app.config["static_consumers"]:
                hostname = get_hostname(gen_service_name(consumer, pr_number))
                if hostname is None:
                    # consumer does not have a PR build, point to master build
                    hostname = get_hostname(gen_service_name(consumer, 0))
                    assert (
                        hostname is not None
                    ), "Invalid static resource consumer service"
                create_subdomain(consumer, pr_number, hostname)
        else:
            assert False, "Unknown deploy type, failed to create PR domains"


def create_subdomain(app_name: str, pr_number: int, hostname: str):
    for _ in range(2):
        try:
            requests.post(
                "https://pr.cs61a.org/create_subdomain",
                json=dict(
                    app=app_name,
                    pr_number=pr_number,
                    pr_host=hostname,
                    secret=get_secret(secret_name="PR_WEBHOOK_SECRET"),
                ),
            )
        except requests.exceptions.ConnectionError:
            # pr_proxy will throw when nginx restarts, but that's just expected
            sleep(5)  # let nginx restart

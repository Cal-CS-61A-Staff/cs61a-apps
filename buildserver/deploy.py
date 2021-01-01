import json
import os
import shutil
from subprocess import CalledProcessError

import sqlalchemy
import sqlalchemy.engine.url

from build import gen_working_dir
from app_config import App, CLOUD_RUN_DEPLOY_TYPES
from common.rpc.hosted import add_domain, new
from common.rpc.secrets import create_master_secret, get_secret, load_all_secrets
from common.shell_utils import sh, tmp_directory
from conf import DB_INSTANCE_NAME, DB_IP_ADDRESS
from pypi_utils import update_setup_py


def gen_master_secret(app: App, pr_number: int):
    public_value, staging_value = create_master_secret(created_app_name=app.name)
    return public_value if pr_number == 0 else staging_value


def gen_env_variables(app: App, pr_number: int):
    if app.config["deploy_type"] == "hosted":
        database_url = sqlalchemy.engine.url.URL(
            drivername="mysql",
            host=DB_IP_ADDRESS,
            username="apps",
            password=get_secret(secret_name="DATABASE_PW"),
            database=app.name.replace("-", "_"),
        ).__to_string__(hide_password=False)
    elif app.config["deploy_type"] in CLOUD_RUN_DEPLOY_TYPES:
        database_url = sqlalchemy.engine.url.URL(
            drivername="mysql+pymysql",
            username="apps",
            password=get_secret(secret_name="DATABASE_PW"),
            database=app.name.replace("-", "_"),
            query={"unix_socket": "{}/{}".format("/cloudsql", DB_INSTANCE_NAME)},
        ).__to_string__(hide_password=False)
    else:
        database_url = None

    return dict(
        ENV="prod",
        DATABASE_URL=database_url,
        INSTANCE_CONNECTION_NAME=DB_INSTANCE_NAME,
        APP_MASTER_SECRET=gen_master_secret(app, pr_number),
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
            "flask-pandas": run_flask_pandas_deploy,
            "docker": run_dockerfile_deploy,
            "pypi": run_pypi_deploy,
            "cloud_function": run_cloud_function_deploy,
            "service": run_service_deploy,
            "static": run_static_deploy,
            "hosted": run_hosted_deploy,
            "none": run_noop_deploy,
        }[app.config["deploy_type"]](app, pr_number)


def run_flask_deploy(app: App, pr_number: int):
    shutil.copy("../../dockerfiles/flask.Dockerfile", "./Dockerfile")
    run_dockerfile_deploy(app, pr_number)


def run_flask_pandas_deploy(app: App, pr_number: int):
    shutil.copy("../../dockerfiles/flask-pandas.Dockerfile", "./Dockerfile")
    run_dockerfile_deploy(app, pr_number)


def build_docker_image(app: App, pr_number: int) -> str:
    for f in os.listdir("../../deploy_files"):
        shutil.copyfile(f"../../deploy_files/{f}", f"./{f}")
    service_name = gen_service_name(app.name, pr_number)
    prod_service_name = gen_service_name(app.name, 0)
    with open("cloudbuild.yaml", "a+") as f:
        f.seek(0)
        contents = f.read()
        contents = contents.replace("PROD_SERVICE_NAME", prod_service_name)
        contents = contents.replace("SERVICE_NAME", service_name)
        f.seek(0)
        f.truncate()
        f.write(contents)
    with open("Dockerfile", "a+") as f:
        f.seek(0)
        contents = f.read()
        contents = contents.replace(
            "<APP_MASTER_SECRET>", gen_master_secret(app, pr_number)
        )
        f.seek(0)
        f.truncate()
        f.write(contents)
    sh("gcloud", "builds", "submit", "-q", "--config", "cloudbuild.yaml")
    return f"gcr.io/cs61a-140900/{service_name}"


def run_dockerfile_deploy(app: App, pr_number: int):
    image = build_docker_image(app, pr_number)
    service_name = gen_service_name(app.name, pr_number)
    sh(
        "gcloud",
        "beta",
        "run",
        "deploy",
        service_name,
        "--image",
        image,
        "--region",
        "us-west1",
        "--platform",
        "managed",
        "--timeout",
        "45m",
        "--cpu",
        str(app.config["cpus"]),
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
    prod_bucket = f"gs://{gen_service_name(app.name, 0)}.buckets.cs61a.org"
    try:
        sh("gsutil", "mb", "-b", "on", bucket)
        # attempt to "pre-warm" bucket with fast intra-bucket transfer
        sh("gsutil", "-m", "rsync", "-dRc", prod_bucket, bucket)
    except CalledProcessError:
        # bucket already exists
        pass
    sh("gsutil", "-m", "rsync", "-dRc", ".", bucket)


def run_service_deploy(app: App, pr_number: int):
    if pr_number != 0:
        return  # do not deploy PR builds to prod!
    for file in os.listdir("."):
        sh(
            "gcloud",
            "compute",
            "scp",
            "--recurse",
            file,
            app.config["service"]["host"] + ":" + app.config["service"]["root"],
            "--zone",
            app.config["service"]["zone"],
        )
    sh(
        "gcloud",
        "compute",
        "ssh",
        app.config["service"]["host"],
        "--command=sudo systemctl restart {}".format(app.config["service"]["name"]),
        "--zone",
        app.config["service"]["zone"],
    )


def run_hosted_deploy(app: App, pr_number: int):
    image = build_docker_image(app, pr_number)
    service_name = gen_service_name(app.name, pr_number)
    new(img=image, name=service_name, env=gen_env_variables(app, pr_number))
    if pr_number == 0:
        for domain in app.config["first_party_domains"]:
            add_domain(name=service_name, domain=domain)


def run_noop_deploy(_app: App, _pr_number: int):
    pass

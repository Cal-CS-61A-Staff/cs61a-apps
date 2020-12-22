import json
from dataclasses import dataclass
from time import sleep
from typing import List
from urllib.parse import urlparse

import requests

from app_config import App, CLOUD_RUN_DEPLOY_TYPES
from common.db import connect_db
from common.rpc.auth import post_slack_message
from common.rpc.hosted import delete, list_apps
from common.rpc.secrets import get_secret
from common.shell_utils import sh
from conf import STATIC_SERVER
from deploy import gen_service_name


class Hostname:
    def to_str(self) -> str:
        raise NotImplemented


@dataclass
class PyPIHostname(Hostname):
    package: str
    version: str

    def to_str(self):
        return f"pypi.org/project/{self.package}/{self.version}"


@dataclass
class PRHostname(Hostname):
    app_name: str
    pr_number: int
    target_hostname: str

    def to_str(self):
        return f"{self.pr_number}.{self.app_name}.pr.cs61a.org"


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

    services = list_apps()
    for service in services:
        if service not in active_service_names:
            delete(name=service)

    if pr_number is not None:
        with connect_db() as db:
            db("DELETE FROM services WHERE pr_number=%s", [pr_number])


def update_service_routes(apps: List[App], pr_number: int):
    if pr_number == 0:
        return  # no updates needed for deploys to master

    for app in apps:
        for hostname in get_pr_subdomains(app, pr_number):
            if isinstance(hostname, PRHostname):
                create_subdomain(
                    hostname.app_name, hostname.pr_number, hostname.target_hostname
                )


def get_pr_subdomains(app: App, pr_number: int) -> List[Hostname]:
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

    def get_hostname(service_name):
        for service in services:
            if service["metadata"]["name"] == service_name:
                return urlparse(service["status"]["address"]["url"]).netloc
        return None

    out = []

    if app.config["deploy_type"] in CLOUD_RUN_DEPLOY_TYPES:
        hostname = get_hostname(gen_service_name(app.name, pr_number))
        assert hostname is not None
        out.append(PRHostname(app.name, pr_number, hostname))
    elif app.config["deploy_type"] == "static":
        for consumer in app.config["static_consumers"]:
            hostname = get_hostname(gen_service_name(consumer, pr_number))
            if hostname is None:
                # consumer does not have a PR build, point to master build
                hostname = get_hostname(gen_service_name(consumer, 0))
                assert hostname is not None, "Invalid static resource consumer service"
            out.append(PRHostname(consumer, pr_number, hostname))
        if not app.config["static_consumers"]:
            out.append(
                PRHostname(app.name, pr_number, gen_service_name(STATIC_SERVER, 0))
            )
    elif app.config["deploy_type"] == "hosted":
        out.append(
            PRHostname(
                app.name,
                pr_number,
                f"{gen_service_name(app.name, pr_number)}.hosted.cs61a.org",
            )
        )
    elif app.config["deploy_type"] == "pypi":
        out.append(PyPIHostname(app.config["package_name"], app.deployed_pypi_version))
    elif app.config["deploy_type"] == "none":
        pass
    else:
        assert False, "Unknown deploy type, failed to create PR domains"

    return out


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

import json
from urllib.parse import urlparse

from deploy import gen_service_name
from shell_utils import sh


def get_base_hostname(app: str) -> str:
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
    for service in services:
        if service["metadata"]["name"] == gen_service_name(app, 0):
            return urlparse(service["status"]["address"]["url"]).netloc
    raise KeyError

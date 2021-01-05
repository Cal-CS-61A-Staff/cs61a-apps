from typing import Dict, Optional

from common.rpc.utils import create_service, requires_master_secret

service = create_service(__name__, "deploy.hosted")


@requires_master_secret
@service.route("/api/list_apps")
def list_apps():
    ...


@requires_master_secret
@service.route("/api/new")
def new(*, img: str, name: Optional[str] = None, env: Dict[str, str] = {}):
    ...


@requires_master_secret
@service.route("/api/stop")
def stop(*, name: str):
    ...


@requires_master_secret
@service.route("/api/run")
def run(*, name: str):
    ...


@requires_master_secret
@service.route("/api/delete")
def delete(*, name: str):
    ...


@requires_master_secret
@service.route("/api/add_domain")
def add_domain(
    *, name: str, domain: str, force: bool = False, proxy_set_header: dict = {}
):
    ...


@requires_master_secret
@service.route("/api/service_log")
def service_log():
    ...


@requires_master_secret
@service.route("/api/container_log")
def container_log(*, name: str):
    ...


@requires_master_secret
@service.route("/api/create_pr_subdomain")
def create_pr_subdomain(*, app: str, pr_number: int, pr_host: str):
    ...

from common.rpc.utils import create_service, requires_master_secret

service = create_service(__name__)


@requires_master_secret
@service.route("/api/clear_queue")
def clear_queue(*, repo: str, pr_number: int):
    ...


@requires_master_secret
@service.route("/api/trigger_build")
def trigger_build_sync(*, pr_number: int, target_app: str = None):
    ...


@requires_master_secret
@service.route("/api/deploy_prod_app_sync")
def deploy_prod_app_sync(*, target_app: str):
    ...


@requires_master_secret
@service.route("/api/get_base_hostname")
def get_base_hostname(*, target_app: str) -> str:
    ...

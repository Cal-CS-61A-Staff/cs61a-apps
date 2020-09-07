from common.rpc.utils import create_service, requires_master_secret

service = create_service(__name__)


@requires_master_secret
@service.route("/api/add_domain")
def add_domain(*, course: str, domain: str):
    ...

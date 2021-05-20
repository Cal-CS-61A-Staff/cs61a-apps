from common.rpc.utils import create_service, requires_master_secret

service = create_service(__name__, "code")


@requires_master_secret
@service.route("/api/create_code_shortlink")
def create_code_shortlink(
    name: str, contents: str, staff_only: bool = True, link: str = None
):
    ...

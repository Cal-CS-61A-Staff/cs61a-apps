from typing import Tuple

from common.rpc.utils import create_service, requires_master_secret

service = create_service("buildserver-hosted-worker")


@requires_master_secret
@service.route("/api/build_worker_build")
def build_worker_build(*, pr_number: int, sha: str) -> Tuple[bool, str]:
    ...

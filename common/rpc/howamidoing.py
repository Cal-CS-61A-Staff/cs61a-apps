from typing import Union

from common.rpc.utils import create_service, requires_master_secret

service = create_service(__name__)


@requires_master_secret
@service.route("/api/upload_grades")
def upload_grades(*, data: str):
    ...

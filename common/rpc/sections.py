from typing import Union

from common.rpc.utils import create_service, requires_master_secret

service = create_service(__name__)


@requires_master_secret
@service.route("/api/export_attendance_rpc")
def rpc_export_attendance(*, full: bool):
    ...

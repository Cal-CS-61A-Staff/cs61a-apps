from typing import Union

from common.rpc.utils import create_service, requires_master_secret

service = create_service(__name__)


@requires_master_secret
@service.route("/api/list_channels")
def list_channels(*, course: str):
    ...


@requires_master_secret
@service.route("/api/post_message")
def post_message(*, course: str, message: Union[str, dict], channel: str):
    ...

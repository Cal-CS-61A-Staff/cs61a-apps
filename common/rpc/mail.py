from typing import Dict

from common.rpc.utils import create_service, requires_master_secret

service = create_service(__name__, providers=["https://cs162.org/autograder/"])


@requires_master_secret
@service.route("/api/send_email")
def send_email(
    *,
    sender: str,
    target: str,
    subject: str,
    body: str,
    attachments: Dict[str, str] = {},
):
    ...

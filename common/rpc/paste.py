from common.rpc.utils import create_service, requires_master_secret

service = create_service(__name__)


@requires_master_secret
@service.route("/api/paste_text")
def paste_text(*, data: str, name: str = None, is_private: bool = False):
    ...


@requires_master_secret
@service.route("/api/get_paste")
def get_paste(*, name: str) -> str:
    ...


def get_paste_url(name: str):
    return f"https://paste.cs61a.org/{name}"

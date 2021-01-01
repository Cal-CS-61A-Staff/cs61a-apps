from typing import Optional

from common.rpc.utils import create_service, requires_access_token

service = create_service(__name__, override="sb")


@requires_access_token
@service.route("/api/update_file")
def update_file(
    *,
    path: str,
    encoded_file_contents: Optional[str] = None,
    symlink: Optional[str] = None,
    delete: bool = False,
):
    ...


@requires_access_token
@service.route("/api/get_server_hashes")
def get_server_hashes():
    ...


@requires_access_token
@service.route("/api/run_make_command", streaming=True)
def run_make_command(*, target: str):
    ...


@requires_access_token
@service.route("/api/is_sandbox_initialized")
def is_sandbox_initialized():
    ...


@requires_access_token
@service.route("/api/initialize_sandbox")
def initialize_sandbox(*, force=True):
    ...

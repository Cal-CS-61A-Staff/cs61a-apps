from typing import List, Dict
from common.rpc.utils import (
    create_service,
    requires_master_secret,
    requires_access_token,
)

service = create_service(__name__, "ag-master")


@requires_master_secret
@service.route("/api/trigger_jobs")
def trigger_jobs(*, assignment_id: str, jobs: List[str]):
    ...


@service.route("/api/get_submission")
def get_submission(*, job_id: str) -> Dict:
    ...


@service.route("/api/handle_output")
def handle_output(*, output: str, job_id: str):
    ...


@service.route("/api/set_failure")
def set_failure(*, job_id: str, result: str):
    ...


@requires_access_token
@service.route("/api/upload_zip")
def upload_zip(*, course: str, name: str, file: str):
    ...


@requires_access_token
@service.route("/api/create_assignment")
def create_assignment(
    *,
    course: str,
    name: str,
    file: str,
    command: str,
    batch_size: int,
    grading_base: str,
) -> str:
    ...

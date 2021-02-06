from typing import List, Dict
from common.rpc.utils import create_service, requires_master_secret

service = create_service(__name__, "ag-master")


@service.route("/api/ok/v3/grade/batch")
def batch_grade(*, subm_ids: List[str], assignment: str, access_token: str):
    ...


@service.route("/results")
def get_results(job_ids: List[str]):
    ...


@requires_master_secret
@service.route("/api/trigger_jobs")
def trigger_jobs(*, assignment_id: str, submissions: List[str], jobs: List[str]):
    ...


@service.route("/api/get_zip")
def get_zip(*, course: str, name: str) -> str:
    ...


@service.route("/api/get_submission")
def get_submission(*, course: str, bid: str, job_id: str) -> Dict:
    ...


@service.route("/api/handle_output")
def handle_output(*, course: str, output: str, job_id: str) -> Dict:
    ...


@service.route("/api/set_results")
def set_results(*, course: str, job_id: str, status: str, result: str):
    ...


@service.route("/api/upload_zip")
def upload_zip(
    *, access_token: str = None, course: str, semester: str, name: str, file: str
):
    ...


@service.route("/api/create_assignment")
def create_assignment(
    *,
    access_token: str = None,
    course: str,
    semester: str,
    name: str,
    file: str,
    command: str
) -> str:
    ...

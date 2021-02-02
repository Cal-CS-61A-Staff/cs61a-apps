from typing import List, Dict
from common.rpc.utils import create_service

service = create_service(__name__, "ag-master")


@service.route("/api/trigger_jobs")
def trigger_jobs(*, secret: str, assignment_id: str, subms: List[str], jobs: List[str]):
    ...


@service.route("/api/get_zip")
def get_zip(*, course: str, name: str) -> str:
    ...


@service.route("/api/get_submission")
def get_submission(*, course: str, bid: str, job_id: str) -> Dict:
    ...


@service.route("/api/send_score")
def send_score(*, course: str, payload: Dict, job_id: str):
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

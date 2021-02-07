from typing import List
from common.rpc.utils import create_service

service = create_service(__name__, "ag-worker")


@service.route("/api/ping_worker")
def ping_worker():
    ...


@service.route("/api/batch_grade")
def batch_grade(*, command: str, jobs: List[str], grading_zip: str):
    ...

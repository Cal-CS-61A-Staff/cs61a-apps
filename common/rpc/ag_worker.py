from typing import List
from common.rpc.utils import create_service

service = create_service(__name__, "ag-worker")


@service.route("/api/batch_grade")
def batch_grade(
    *,
    secret: str,
    assignment_id: str,
    assignment_name: str,
    command: str,
    backups: List[str],
    jobs: List[str],
    course_key: str
):
    ...

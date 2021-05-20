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
    """Given a list of job IDs, queues autograder workers to begin grading.

    :param assignment_id: the assignment secret key, used as an identifier
    :type assignment_id: str
    :param jobs: the list of job IDs to queue
    :type jobs: list[str]

    Bound in :func:`~docs.ag_master.okpy.create_okpy_endpoints`
    """
    ...


@service.route("/api/get_submission")
def get_submission(*, job_id: str) -> Dict:
    """Given a job ID, gets submission information from Okpy and forwards it
    to the requesting worker.

    :param job_id: the job ID associated with the requested backup
    :type job_id: str

    :return: a dictionary containing backup information, specifically the
        ``data`` value `here <https://okpy.github.io/documentation/ok-api.html#backups-view-a-backup>`_

    Bound in :func:`~docs.ag_master.worker.create_worker_endpoints`
    """
    ...


@service.route("/api/handle_output")
def handle_output(*, output: str, job_id: str):
    """Given output and a job ID, parses the output for scores and uploads them
    to Okpy. See :class:`~docs.ag_master.worker` for helper functions used.

    :param output: the autograder worker output
    :type output: str
    :param job_id: the job ID associated with the output
    :type job_id: str

    Bound in :func:`~docs.ag_master.worker.create_worker_endpoints`
    """
    ...


@service.route("/api/set_failure")
def set_failure(*, job_id: str, result: str):
    """Given a job ID and some output result, set the job to failed and report
    the failure to Okpy.

    :param job_id: the job ID associated with the output
    :type job_id: str
    :param result: the autograder worker output
    :type result: str

    Bound in :func:`~docs.ag_master.worker.create_worker_endpoints`
    """
    ...


@requires_access_token
@service.route("/api/upload_zip")
def upload_zip(*, course: str, name: str, file: str):
    """Given a course, a filename, and base64-encoded zip file contents,
    upload the file to a cloud storage bucket. This method is meant to be
    accessed using the SICP command-line tool.

    :param course: the course code
    :type course: str
    :param name: the filename
    :type name: str
    :param file: base64-encoded zip-file contexts
    :type file: str

    Bound in :func:`~docs.ag_master.admin.create_admin_endpoints`
    """
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
    """Given some information about an assignment, register it into the
    autograder database so that it may be graded using the autograder. This
    method is meant to be accessed using the SICP command-line tool.

    :param course: the course code
    :type course: str
    :param name: the assignment shortname
    :type name: str
    :param file: the assignment filename (should be the same as ``name`` in
        :func:`~common.rpc.ag_master.upload_zip`)
    :type file: str
    :param command: the command the worker should run to grade a backup for this
        assignment
    :type command: str
    :param batch_size: how many backups should be graded by one worker
    :type batch_size: int
    :param grading_base: the grading server associated with the assignment
        (by default, https://okpy.org)
    :type grading_base: str

    Bound in :func:`~docs.ag_master.admin.create_admin_endpoints`
    """
    ...

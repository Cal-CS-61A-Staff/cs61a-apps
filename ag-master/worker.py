from functools import wraps
from typing import List, Union

import requests
import time

from common.rpc.ag_master import get_submission, handle_output, set_failure
from models import Job, db
from utils import SCORE_ENDPOINT, SUBM_ENDPOINT


def job_transition(*, at: Union[str, List[str]], to: str):
    def decorator(func):
        @wraps(func)
        def handler(*, job_id, **kwargs):
            job = Job.query.get(job_id)
            if not job:
                raise KeyError
            if isinstance(at, str):
                at_list = [at]
            else:
                at_list = at
            if job.status not in at_list:
                raise PermissionError
            try:
                return func(job=job, **kwargs)
            finally:
                job.status = to
                db.session.commit()

        return handler

    return decorator


def create_worker_endpoints(app):
    @get_submission.bind(app)
    @job_transition(at="queued", to="started")
    def get_submission_rpc(job):
        r = requests.get(
            f"{job.assignment.grading_base}{SUBM_ENDPOINT}/{job.backup}",
            params=dict(access_token=job.access_token),
        )
        job.started_at = int(time.time())
        db.session.commit()

        r.raise_for_status()
        return r.json()["data"]

    @handle_output.bind(app)
    @job_transition(at="started", to="finished")
    def handle_output_rpc(output, job):
        scores = parse_scores(output)
        for score in scores:
            score["bid"] = job.backup
            requests.post(
                job.assignment.grading_base + SCORE_ENDPOINT,
                data=score,
                params=dict(access_token=job.access_token),
            )
        job.result = output
        job.finished_at = int(time.time())
        db.session.commit()

    @set_failure.bind(app)
    @job_transition(at=["queued", "started"], to="failed")
    def set_failure_rpc(job, result):
        job.result = result
        job.finished_at = int(time.time())
        db.session.commit()


def extract_scores(transcript):
    """Return a list of (key, score) pairs from a transcript, raising
    ValueErrors."""

    score_lines = []
    found_score = False
    for line in reversed(transcript.split("\n")):
        line = line.strip()
        if line.lower() == "score:":
            found_score = True
            break
        if ":" in line:
            score_lines.append(line)

    if not found_score:
        raise ValueError('no scores found; "Score" must appear on a line by ' "itself")

    pairs = [l.split(":", 1) for l in reversed(score_lines)]

    if len(pairs) == 0:
        raise ValueError('no scores found; "Score" must be followed with a ' "colon")

    return [(k, float(v)) for k, v in pairs]


def parse_scores(output):
    all_scores = []
    try:
        scores = extract_scores(output)
        for name, points in scores:
            if len(output) > 9000:
                output = (
                    output[:750]
                    + "\nTruncated "
                    + str(len(output) - 1500)
                    + " Characters.\n"
                    + output[-750:]
                )

            all_scores.append(
                {"score": float(points), "kind": name, "message": str(output)}
            )
    except ValueError as e:
        message = "Error - Parse: " + str(e) + "Got: \n{}".format(output)
        return [{"score": 0.0, "kind": "Error", "message": message}]

    return all_scores

import requests

from common.rpc.ag_master import get_submission, handle_output, set_results
from models import Assignment, Job, db
from utils import SCORE_ENDPOINT, SUBM_ENDPOINT


def create_worker_endpoints(app):
    @get_submission.bind(app)
    def get_submission_rpc(bid, job_id):
        # @nocommit these should all support batch queries
        job = Job.query.get(job_key=job_id)
        if not job:
            raise KeyError
        r = requests.get(
            SUBM_ENDPOINT + "/" + str(bid),
            params=dict(access_token=job.access_token),
        )
        r.raise_for_status()
        return r.json()["data"]

    @handle_output.bind(app)
    def handle_output_rpc(output, job_id):
        job = Job.query.get(job_id)
        if not job:
            raise KeyError
        scores = parse_scores(output)
        for score in scores:
            score["bid"] = job.backup
            requests.post(
                SCORE_ENDPOINT,
                data=score,
                params=dict(access_token=job.access_token),
            )

    @set_results.bind(app)
    def set_results_rpc(job_id, status, result):
        job = Job.query.get(job_id)
        if not job:
            raise KeyError
        job.status = status
        job.result = result
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

import tempfile, requests, base64
from google.cloud import storage

from models import Assignment, Job, db
from utils import check_course_secret, BUCKET, SUBM_ENDPOINT, SCORE_ENDPOINT

from common.rpc.ag_master import get_zip, get_submission, handle_output, set_results


def create_worker_endpoints(app):
    @get_zip.bind(app)
    @check_course_secret
    def get_zip_rpc(course, name):
        assignment = Assignment.query.filter_by(name=name, course=course.secret).first()
        if assignment:
            bucket = storage.Client().get_bucket(BUCKET)
            blob = bucket.blob(
                f"zips/{course.name}-{course.semester}/{assignment.file}"
            )
            with tempfile.NamedTemporaryFile() as temp:
                blob.download_to_filename(temp.name)
                with open(temp.name, "rb") as zf:
                    return base64.b64encode(zf.read()).decode("ascii")
        raise PermissionError

    @get_submission.bind(app)
    @check_course_secret
    def get_submission_rpc(course, bid, job_id):
        job = Job.query.filter_by(job_key=job_id).first()
        assignment = Assignment.query.filter_by(
            ag_key=job.assignment, course=course.secret
        ).first()  # validates secret
        if job and assignment:
            r = requests.get(
                SUBM_ENDPOINT + "/" + str(bid),
                params=dict(access_token=job.access_token),
            )
            r.raise_for_status()
            return r.json()["data"]
        return dict(success=False)

    @handle_output.bind(app)
    @check_course_secret
    def handle_output_rpc(course, output, job_id):
        job = Job.query.filter_by(job_key=job_id).first()
        assignment = Assignment.query.filter_by(
            ag_key=job.assignment, course=course.secret
        ).first()  # validates secret
        if job and assignment:
            scores = parse_scores(output)
            for score in scores:
                score["bid"] = job.backup
                requests.post(
                    SCORE_ENDPOINT,
                    data=score,
                    params=dict(access_token=job.access_token),
                )
        return dict(success=(job is not None))

    @set_results.bind(app)
    @check_course_secret
    def set_results_rpc(course, job_id, status, result):
        job = Job.query.filter_by(job_key=job_id).first()
        assignment = Assignment.query.filter_by(
            ag_key=job.assignment, course=course.secret
        ).first()  # validates secret
        if job and assignment:
            job.status = status
            job.result = result
            db.session.commit()
        return dict(success=(job is not None))


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

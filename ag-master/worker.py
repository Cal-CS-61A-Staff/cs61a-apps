import tempfile, requests, base64
from google.cloud import storage

from models import Assignment, Job, db
from utils import check_course_secret, BUCKET, SUBM_ENDPOINT, SCORE_ENDPOINT

from common.rpc.ag_master import get_zip, get_submission, send_score, set_results


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

    @send_score.bind(app)
    @check_course_secret
    def send_score_rpc(course, payload, job_id):
        job = Job.query.filter_by(job_key=job_id).first()
        assignment = Assignment.query.filter_by(
            ag_key=job.assignment, course=course.secret
        ).first()  # validates secret
        if job and assignment:
            requests.post(
                SCORE_ENDPOINT, data=payload, params=dict(access_token=job.access_token)
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

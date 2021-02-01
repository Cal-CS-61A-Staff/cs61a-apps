import tempfile, requests
from flask import Blueprint, request, abort, send_file
from google.cloud import storage

from models import Assignment, Job
from utils import check_course_secret, BUCKET, SUBM_ENDPOINT, SCORE_ENDPOINT


def create_worker_endpoints(db):
    app = Blueprint("worker")

    @app.route("/get_zip", methods=["POST"])
    @check_course_secret
    def get_zip(course):
        assignment = Assignment.query.filter_by(
            name=request.json["name"], course=course.secret
        ).first()
        if assignment:
            bucket = storage.Client().get_bucket(BUCKET)
            blob = bucket.blob(
                f"zips/{course.name}-{course.semester}/{assignment.file}"
            )
            with tempfile.NamedTemporaryFile() as temp:
                blob.download_to_filename(temp.name)
                return send_file(temp.name)
        abort(404)

    @app.route("/get_submission", methods=["POST"])
    @check_course_secret
    def get_submission(course):
        data = request.json
        id = data["id"]
        job = Job.query.filter_by(job_key=data["job_id"]).first()
        assignment = Assignment.query.filter_by(
            ag_key=job.assignment, course=course.secret
        ).first()  # validates secret
        if job and assignment:
            r = requests.get(
                SUBM_ENDPOINT + "/" + str(id),
                params=dict(access_token=job.access_token),
            )
            r.raise_for_status()
            return r.json()
        return dict(success=False)

    @app.route("/send_score", methods=["POST"])
    @check_course_secret
    def send_score(course):
        data = request.json
        payload = data["payload"]
        job = Job.query.filter_by(job_key=data["job_id"]).first()
        assignment = Assignment.query.filter_by(
            ag_key=job.assignment, course=course.secret
        ).first()  # validates secret
        if job and assignment:
            requests.post(
                SCORE_ENDPOINT, data=payload, params=dict(access_token=job.access_token)
            )
        return dict(success=(job is not None))

    @app.route("/set_results", methods=["POST"])
    @check_course_secret
    def set_results(course):
        data = request.json
        job = Job.query.filter_by(job_key=data["job_id"]).first()
        assignment = Assignment.query.filter_by(
            ag_key=job.assignment, course=course.secret
        ).first()  # validates secret
        if job and assignment:
            job.status = data["status"]
            job.result = data["result"]
            db.session.commit()
        return dict(success=(job is not None))

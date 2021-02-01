import requests
from flask import Blueprint, request, abort
from werkzeug.security import gen_salt

from common.rpc.secrets import get_secret

from models import Assignment, Job
from utils import check_master_secret, MASTER_URL, WORKER_URL, BATCH_SIZE


def create_okpy_endpoints(db):
    app = Blueprint("okpy")

    @app.route("/api/ok/v3/grade/batch", methods=["POST"])
    def batch_grade():
        data = request.json
        subms = data["subm_ids"]
        assignment_id = data["assignment"]
        if assignment_id == "test":
            return "OK"
        ok_token = data["access_token"]

        assignment = Assignment.query.filter_by(ag_key=assignment_id).first()
        if not assignment:
            abort(404, "Unknown Assignment")

        jobs = [gen_salt(24) for _ in subms]

        objects = [
            Job(
                assignment=assignment.ag_key,
                backup=id,
                status="queued",
                job_key=job_id,
                access_token=ok_token,
            )
            for id, job_id in zip(subms, jobs)
        ]
        db.session.bulk_save_objects(objects)
        db.session.commit()

        try:
            requests.post(
                f"{MASTER_URL}/trigger_jobs",
                json=dict(
                    assignment_id=assignment_id,
                    subms=subms,
                    jobs=jobs,
                ),
                headers=dict(Authorization=get_secret(secret_name="AG_MASTER_SECRET")),
                timeout=1,
            )
        except requests.exceptions.ReadTimeout:
            pass

        return dict(jobs=jobs)

    @app.route("/trigger_jobs", methods=["POST"])
    @check_master_secret
    def trigger_jobs():
        data = request.json
        assignment_id = data["assignment_id"]
        subms = data["subms"]
        jobs = data["jobs"]

        assignment = Assignment.query.filter_by(ag_key=assignment_id).first()
        if not assignment:
            abort(404, "Unknown Assignment")

        subm_batches = [
            subms[i : i + BATCH_SIZE] for i in range(0, len(subms), BATCH_SIZE)
        ]
        job_batches = [
            jobs[i : i + BATCH_SIZE] for i in range(0, len(jobs), BATCH_SIZE)
        ]

        for subm_batch, job_batch in zip(subm_batches, job_batches):
            trigger_job_batch(assignment, subm_batch, job_batch)
        return dict(success=True)

    def trigger_job_batch(assignment, ids, jobs):
        try:
            requests.post(
                f"{WORKER_URL}/batch_grade",
                json=dict(
                    assignment_id=assignment.ag_key,
                    assignment_name=assignment.name,
                    command=assignment.command,
                    jobs=jobs,
                    backups=ids,
                    course_key=assignment.course,
                ),
                headers=dict(Authorization=get_secret(secret_name="AG_WORKER_SECRET")),
                timeout=1,
            )
        except requests.exceptions.ReadTimeout:
            pass
        return jobs

    @app.route("/results/<job_id>", methods=["GET"])
    def get_results_for(job_id):
        job = Job.query.filter_by(job_key=job_id).first()
        if job and job.status in ("finished", "failed"):
            return job.status, 200
        return "Nope!", 202

    @app.route("/results", methods=["POST"])
    def get_results():
        job_ids = request.json
        jobs = Job.query.filter(Job.job_key.in_(job_ids)).all()

        res = {job.job_key: dict(status=job.status, result=job.result) for job in jobs}
        for job in job_ids:
            if job not in res:
                res[job] = None

        return res

    return app

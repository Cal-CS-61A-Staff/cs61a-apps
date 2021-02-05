from flask import request, abort
from werkzeug.security import gen_salt

from common.rpc.secrets import get_secret
from common.rpc.ag_master import trigger_jobs
from common.rpc.ag_worker import batch_grade

from models import Assignment, Job, db
from utils import BATCH_SIZE


def create_okpy_endpoints(app):
    @app.route("/api/ok/v3/grade/batch", methods=["POST"])
    def okpy_receiver():
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

        trigger_jobs(
            secret=get_secret(secret_name="AG_MASTER_SECRET"),
            assignment_id=assignment_id,
            subms=subms,
            jobs=jobs,
            noreply=True,
        )

        return dict(jobs=jobs)

    @trigger_jobs.bind(app)
    def trigger_jobs_rpc(secret, assignment_id, subms, jobs):
        if secret != get_secret(secret_name="AG_MASTER_SECRET"):
            raise PermissionError

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
            if not trigger(assignment, subm_batch, job_batch):
                trigger(assignment, subm_batch, job_batch)
        return dict(success=True)

    def trigger(assignment, subm, jobs):
        for line in batch_grade(
            assignment_id=assignment.ag_key,
            assignment_name=assignment.name,
            command=assignment.command,
            backups=subm,
            jobs=jobs,
            course_key=assignment.course,
            secret=get_secret(secret_name="AG_WORKER_SECRET"),
        ):
            if line == "started":
                return True
        return False

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

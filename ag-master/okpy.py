import base64
import tempfile
import traceback
from typing import Optional

from flask import abort, request
from google.cloud import storage

from common.rpc.ag_master import trigger_jobs
from common.rpc.ag_worker import batch_grade
from common.rpc.auth import get_endpoint
from common.rpc.secrets import only
from common.secrets import new_secret
from models import Assignment, Job, db
from utils import BATCH_SIZE, BUCKET


def create_okpy_endpoints(app):
    @app.route("/api/ok/v3/grade/batch", methods=["POST"])
    def okpy_batch_grade_impl():
        data = request.json
        subm_ids = data["subm_ids"]
        assignment = data["assignment"]
        access_token = data["access_token"]

        if assignment == "test":
            return "OK"

        assignment: Optional[Assignment] = Assignment.query.get(assignment)
        if not assignment or assignment.endpoint != get_endpoint(
            course=assignment.course
        ):
            abort(404, "Unknown Assignment")

        job_secrets = [new_secret() for _ in subm_ids]

        jobs = [
            Job(
                assignment_secret=assignment.assignment_secret,
                backup=backup_id,
                status="queued",
                job_secret=job_secret,
                external_job_id=new_secret(),
                access_token=access_token,
            )
            for backup_id, job_secret in zip(subm_ids, job_secrets)
        ]
        db.session.bulk_save_objects(jobs)
        db.session.commit()

        trigger_jobs(
            assignment_id=assignment.assignment_secret, jobs=job_secrets, noreply=True
        )

        return dict(jobs=[job.external_job_id for job in jobs])

    @trigger_jobs.bind(app)
    @only("ag-master")
    def trigger_jobs_impl(assignment_id, jobs):
        job_batches = [
            jobs[i : i + BATCH_SIZE] for i in range(0, len(jobs), BATCH_SIZE)
        ]
        assignment: Assignment = Assignment.query.get(assignment_id)

        bucket = storage.Client().get_bucket(BUCKET)
        blob = bucket.blob(f"zips/{assignment.endpoint}/{assignment.file}")
        with tempfile.NamedTemporaryFile() as temp:
            blob.download_to_filename(temp.name)
            with open(temp.name, "rb") as zf:
                encoded_zip = base64.b64encode(zf.read()).decode("ascii")

        for job_batch in job_batches:
            try:
                batch_grade(
                    command=assignment.command,
                    jobs=job_batch,
                    grading_zip=encoded_zip,
                    noreply=True,
                    timeout=8,
                )
            except:
                # @nocommit this is somehow wrong because it errored in a PR build
                Job.query.filter(Job.job_key.in_(job_batch)).update(
                    {
                        Job.status: "failed",
                        Job.result: "trigger_job error\n" + traceback.format_exc(),
                    }
                )
                db.session.commit()

    @app.route("/results/<job_id>", methods=["GET"])
    def get_results_for(job_id):
        job = Job.query.filter_by(external_job_id=job_id).one()
        if job.status in ("finished", "failed"):
            return job.result, 200
        return "Nope!", 202

    @app.route("/results", methods=["POST"])
    def get_results_impl():
        job_ids = request.json
        jobs = Job.query.filter(Job.external_job_id.in_(job_ids)).all()

        res = {
            job.external_job_id: dict(status=job.status, result=job.result)
            for job in jobs
        }
        for job in job_ids:
            if job not in res:
                res[job] = None

        return res

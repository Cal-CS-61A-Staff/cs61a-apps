import base64
import tempfile
import traceback

from flask import abort
from google.cloud import storage

from common.rpc.ag_master import get_results, okpy_batch_grade, trigger_jobs
from common.rpc.ag_worker import batch_grade
from common.rpc.secrets import only
from common.secrets import new_secret
from models import Assignment, Job, db
from utils import BATCH_SIZE, BUCKET


def create_okpy_endpoints(app):
    @okpy_batch_grade.bind(app)
    def okpy_batch_grade_impl(subm_ids, assignment, access_token):
        if assignment == "test":
            # @nocommit can this be jsonified safely?
            return "OK"

        assignment: Assignment = Assignment.query.get(assignment)
        if assignment is None:
            abort(404, "Unknown Assignment")

        jobs = [new_secret() for _ in subm_ids]

        objects = [
            Job(
                assignment=assignment,
                backup=backup_id,
                status="queued",
                job_secret=job_id,
                external_job_id=new_secret(),
                access_token=access_token,
            )
            for backup_id, job_id in zip(subm_ids, jobs)
        ]
        db.session.bulk_save_objects(objects)
        db.session.commit()

        trigger_jobs(
            assignment_id=assignment.assignment_secret, jobs=jobs, noreply=True
        )

        return dict(jobs=jobs)

    @trigger_jobs.bind(app)
    @only("ag-master")
    def trigger_jobs_impl(assignment_id, jobs):
        job_batches = [jobs[i : i + BATCH_SIZE] for i in range(len(jobs), BATCH_SIZE)]
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
                    jobs=jobs,
                    grading_zip=encoded_zip,
                    noreply=True,
                    timeout=7,
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
        return dict(success=True)

    @app.route("/results/<job_id>", methods=["GET"])
    def get_results_for(job_id):
        job = Job.query.filter_by(job_key=job_id).one()
        if job.status in ("finished", "failed"):
            return job.result, 200
        return "Nope!", 202

    @get_results.bind(app)
    def get_results_impl(job_ids):
        jobs = Job.query.filter(Job.job_key.in_(job_ids)).all()

        res = {job.job_key: dict(status=job.status, result=job.result) for job in jobs}
        for job in job_ids:
            if job not in res:
                res[job] = None

        return res

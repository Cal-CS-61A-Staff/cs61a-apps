import base64
import time

from google.cloud import storage
from typing import List
from flask import request, render_template
from datetime import datetime

from common.rpc.ag_master import create_assignment, upload_zip
from common.rpc.auth import get_endpoint
from common.secrets import new_secret
from common.oauth_client import get_user

from models import Assignment, db, Job
from utils import BUCKET, admin_only


def create_admin_endpoints(app):
    @upload_zip.bind(app)
    @admin_only
    def upload_zip_rpc(course, name, file):
        file = base64.b64decode(file.encode("ascii"))
        bucket = storage.Client().get_bucket(BUCKET)
        blob = bucket.blob(f"zips/{get_endpoint(course=course)}/{name}")
        blob.upload_from_string(file, content_type="application/zip")

    @create_assignment.bind(app)
    @admin_only
    def create_assignment_rpc(course, name, file, command):
        assignment: Assignment = Assignment.query.filter_by(
            name=name, course=course, endpoint=get_endpoint(course=course)
        ).one_or_none()

        if not assignment:
            assignment = Assignment(
                name=name,
                assignment_secret=new_secret(),
                course=course,
                endpoint=get_endpoint(course=course),
            )
            db.session.add(assignment)

        assignment.file = file
        assignment.command = command
        assignment.last_modified = int(time.time())
        db.session.commit()

        return assignment.assignment_secret

    @app.template_filter("dt")
    def format_dt(value, format="%b %d, %Y at %I:%M %p"):
        if value is None:
            return "no date provided"
        return datetime.fromtimestamp(int(value)).strftime(format)

    @app.route("/<course>")
    @app.route("/<course>/assignments")
    @admin_only
    def get_assignments(course):
        endpoint = get_endpoint(course=course)
        assignments: List[Assignment] = Assignment.query.filter(
            Assignment.endpoint == endpoint
        ).all()

        return render_template(
            "assignments.html", course=course, assignments=assignments
        )

    @app.route("/<course>/fail_pending", methods=["POST"])
    @admin_only
    def fail_pending_jobs(course):
        endpoint = get_endpoint(course=course)
        jobs = (
            Job.query.join(Assignment)
            .filter(Assignment.endpoint == endpoint)
            .filter(Job.status == "queued")
            .all()
        )

        count = Job.query.filter(
            Job.job_secret.in_([job.job_secret for job in jobs])
        ).update(
            {
                Job.status: "failed",
                Job.finished_at: int(time.time()),
                Job.result: f"Marked as failed by {get_user()['email']}.",
            },
            synchronize_session="fetch",
        )
        db.session.commit()

        return dict(modified=count)

    @app.route("/<course>/<assign>/jobs")
    @admin_only
    def get_jobs(course, assign):
        endpoint = get_endpoint(course=course)
        jobs: List[Job] = (
            Job.query.join(Assignment)
            .filter(Assignment.endpoint == endpoint)
            .filter(Assignment.name == assign)
        )

        queued_at = request.args.get("queued_at", 0)
        if queued_at:
            jobs = jobs.filter(Job.queued_at == queued_at)

        status = request.args.get("status", "all")
        if status != "all":
            jobs = jobs.filter(Job.status == status)
        jobs = jobs.all()

        batches = {}
        for job in jobs:
            if str(job.queued_at) not in batches:
                batches[str(job.queued_at)] = {
                    "jobs": [],
                    "finished": 0,
                    "failed": 0,
                    "running": 0,
                    "queued": 0,
                    "completed": 0,
                    "total": 0,
                }
            batch = batches[str(job.queued_at)]

            details = {
                "started_at": job.started_at,
                "finished_at": job.finished_at,
                "backup": job.backup,
                "status": job.status,
                "result": job.result,
                "id": job.external_job_id,
            }

            if details["finished_at"]:
                if details["status"] == "finished":
                    batch["finished"] += 1
                    details["duration"] = details["finished_at"] - details["started_at"]
                else:
                    batch["failed"] += 1
                batch["completed"] += 1
            elif details["started_at"]:
                batch["running"] += 1
            else:
                batch["queued"] += 1

            batch["total"] += 1
            batch["progress"] = batch["completed"] / batch["total"]
            batch["jobs"].append(details)

        return render_template(
            "jobs.html",
            course=course,
            assign=assign,
            batches={k: batches[k] for k in sorted(batches, reverse=True)},
            queued_at=str(queued_at),
            status=status,
        )

    @app.route("/<course>/job/<id>")
    @admin_only
    def job_details(course, id):
        endpoint = get_endpoint(course=course)
        job: Job = (
            Job.query.join(Assignment)
            .filter(Assignment.endpoint == endpoint)
            .filter(Job.external_job_id == id)
            .one()
        )

        return render_template(
            "job.html",
            course=course,
            backup=job.backup,
            status=job.status,
            result=job.result,
            start=job.started_at,
            finish=job.finished_at,
        )

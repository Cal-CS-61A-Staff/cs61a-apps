import base64
import time

from google.cloud import storage
from typing import List
from flask import jsonify, request

from common.rpc.ag_master import create_assignment, upload_zip
from common.rpc.auth import get_endpoint
from common.secrets import new_secret
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

    @app.route("/<course>/assignments")
    @admin_only
    def get_assignments(course):
        endpoint = get_endpoint(course=course)
        assignments: List[Assignment] = Assignment.query.filter(
            Assignment.endpoint == endpoint
        ).all()

        return {
            assign.name: {
                "last_modified": assign.last_modified,
            }
            for assign in assignments
        }

    @app.route("/<course>/fail_pending")
    @admin_only
    def fail_pending_jobs(course):
        endpoint = get_endpoint(course=course)
        jobs = (
            Job.query.join(Assignment)
            .filter(Assignment.endpoint == endpoint)
            .filter(Job.status == "queued")
            .all()
        )
        for job in jobs:
            job.status = "failed"
            job.finished_at = int(time.time())
        db.session.commit()

        return dict(modified=len(jobs))

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
            if job.queued_at not in batches:
                batches[job.queued_at] = {
                    "jobs": [],
                    "finished": 0,
                    "failed": 0,
                    "running": 0,
                    "queued": 0,
                }

            details = {
                "started_at": job.started_at,
                "finished_at": job.finished_at,
                "backup": job.backup,
                "status": job.status,
                "result": job.result,
            }

            if details["finished_at"]:
                if details["status"] == "finished":
                    batches[job.queued_at]["finished"] += 1
                    details["duration"] = details["finished_at"] - details["started_at"]
                else:
                    batches[job.queued_at]["failed"] += 1
            elif details["started_at"]:
                batches[job.queued_at]["running"] += 1
            else:
                batches[job.queued_at]["queued"] += 1

            batches[job.queued_at]["progress"] = (
                batches[job.queued_at]["finished"] + batches[job.queued_at]["failed"]
            ) / (
                batches[job.queued_at]["finished"]
                + batches[job.queued_at]["failed"]
                + batches[job.queued_at]["running"]
                + batches[job.queued_at]["queued"]
            )
            batches[job.queued_at]["jobs"].append(details)

        return batches

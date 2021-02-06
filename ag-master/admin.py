import base64
import time

from google.cloud import storage
from typing import List
from flask import jsonify

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

    @app.route("/<course>/<assign>/jobs")
    @admin_only
    def get_jobs(course, assign):
        endpoint = get_endpoint(course=course)
        assign = (
            Assignment.query.filter(Assignment.endpoint == endpoint)
            .filter(Assignment.name == assign)
            .one()
        )
        jobs: List[Job] = Job.query.filter(
            Job.assignment_secret == assign.assignment_secret
        ).all()

        return jsonify(
            [
                {
                    "queued_at": job.queued_at,
                    "started_at": job.started_at,
                    "finished_at": job.finished_at,
                    "backup": job.backup,
                    "status": job.status,
                    "result": job.result,
                }
                for job in jobs
            ]
        )

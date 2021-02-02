import base64
from flask import request, abort
from google.cloud import storage
from werkzeug.security import gen_salt

from models import Assignment, Job
from utils import admin_only, admin_only_rpc, BUCKET

from common.rpc.ag_master import upload_zip, create_assignment


def create_admin_endpoints(app, db):
    @upload_zip.bind(app)
    @admin_only_rpc
    def upload_zip_rpc(course, name, file):
        file = base64.b64decode(file.encode("ascii"))
        bucket = storage.Client().get_bucket(BUCKET)
        blob = bucket.blob(f"zips/{course.name}-{course.semester}/{name}")
        blob.upload_from_string(file, content_type="application/zip")
        return dict(success=True)

    @create_assignment.bind(app)
    @admin_only_rpc
    def create_assignment_rpc(course, name, file, command):
        existing = Assignment.query.filter_by(name=name, course=course.secret).first()
        if existing:
            existing.file = file
            existing.command = command
            db.session.commit()
            return dict(assign_id=existing.ag_key)

        id = gen_salt(24)
        existing = Assignment(
            name=name, course=course.secret, file=file, command=command, ag_key=id
        )
        db.session.add(existing)
        db.session.commit()

        return id

    @app.route("/jobs/<job>")
    @admin_only
    def job_info(course, job):
        job = Job.query.filter_by(job_key=job).first()
        if not job:
            abort(404)

        assignment = Assignment.query.filter_by(ag_key=job.assignment).first()
        if not assignment or assignment.course != course.secret:
            abort(403)

        return {
            "assignment": assignment.name,
            "backup": job.backup,
            "status": job.status,
            "result": job.result,
        }

    @app.route("/course_info")
    @app.route("/")
    @admin_only
    def course_info(course):
        assignments = Assignment.query.filter_by(course=course.secret).all()
        return {
            "assignments": [
                {
                    "name": a.name,
                    "file": a.file,
                    "command": a.command,
                    "ag_key": a.ag_key,
                }
                for a in assignments
            ]
        }

import base64

from google.cloud import storage

from common.rpc.ag_master import create_assignment, upload_zip
from common.rpc.auth import get_endpoint
from common.secrets import new_secret
from models import Assignment, db
from utils import BUCKET, admin_only


def create_admin_endpoints(app):
    @upload_zip.bind(app)
    @admin_only
    def upload_zip_rpc(course, name, file):
        file = base64.b64decode(file.encode("ascii"))
        bucket = storage.Client().get_bucket(BUCKET)
        blob = bucket.blob(f"zips/{get_endpoint(course=course)}/{name}")
        blob.upload_from_string(file, content_type="application/zip")
        return dict(success=True)

    @create_assignment.bind(app)
    @admin_only
    def create_assignment_rpc(course, name, file, command):
        assignment: Assignment = Assignment.query.filter_by(
            name=name,
            course=course,
        ).one_or_none()

        if not assignment:
            assignment = Assignment(name=name, assignment_secret=new_secret())
            db.session.add(assignment)

        assignment.file = file
        assignment.command = command
        db.session.commit()

        return assignment.assignment_secret

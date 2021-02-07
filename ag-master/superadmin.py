from models import Assignment
from utils import super_admin_only


def create_superadmin_endpoints(app):
    @app.route("/admin/<endpoint>")
    @super_admin_only
    def course_info_admin(endpoint):
        assignments = Assignment.query.filter_by(endpoint=endpoint).all()
        return {
            "assignments": [
                {
                    "name": a.name,
                    "file": a.file,
                    "command": a.command,
                    "assignment_secret": a.assignment_secret,
                }
                for a in assignments
            ],
        }

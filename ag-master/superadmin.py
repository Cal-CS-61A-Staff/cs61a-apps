from flask import request, abort
from werkzeug.security import gen_salt

from utils import superadmin_only
from models import Course, Assignment


def create_superadmin_endpoints(app, db):
    @app.route("/admin/courses")
    @superadmin_only
    def course_list():
        courses = Course.query.all()
        return dict(
            success=True,
            courses=[
                {
                    "name": c.name,
                    "semester": c.semester,
                }
                for c in courses
            ],
        )

    @app.route("/admin/courses/<semester>")
    @superadmin_only
    def courses_in(semester):
        courses = Course.query.filter_by(semester=semester).all()
        return dict(
            success=True,
            courses=[
                {
                    "name": c.name,
                    "semester": c.semester,
                }
                for c in courses
            ],
        )

    @app.route("/admin/<course>/<semester>")
    @superadmin_only
    def course_info_admin(course, semester):
        course = Course.query.filter_by(name=course, semester=semester).first()
        if not course:
            abort(404)
        assignments = Assignment.query.filter_by(course=course.secret)
        return {
            "secret": course.secret,
            "assignments": [
                {
                    "name": a.name,
                    "file": a.file,
                    "command": a.command,
                    "ag_key": a.ag_key,
                }
                for a in assignments
            ],
        }

    @app.route("/admin/create_course", methods=["POST"])
    @superadmin_only
    def create_course():
        data = request.json
        name = data["name"]
        sem = data["semester"]

        existing = Course.query.filter_by(name=name, semester=sem).first()
        if existing:
            return (
                "This course already exists. If you've misplaced your master key, contact a 61A admin!",
                400,
            )

        secret = gen_salt(24)
        db.session.add(Course(name=name, semester=sem, secret=secret))
        db.session.commit()

        return dict(success=True, name=name, semester=sem, secret=secret)

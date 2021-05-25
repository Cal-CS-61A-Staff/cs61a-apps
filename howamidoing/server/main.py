import json
import os
import sys

from common.course_config import get_course
from common.db import connect_db, transaction_db
from common.oauth_client import create_oauth_client, get_user, is_logged_in, is_staff
from common.rpc.howamidoing import upload_grades as rpc_upload_grades
from common.rpc.secrets import only
from common.rpc.auth import is_admin, validate_secret
from setup_functions import set_default_config, set_grades

from flask import Flask, redirect, request, jsonify, render_template, Response

CONSUMER_KEY = "61a-grade-view"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

AUTHORIZED_ROLES = ["staff", "instructor", "grader"]

DEV = os.getenv("ENV") != "prod"

IS_SPHINX = "sphinx" in sys.argv[0]


with connect_db() as db:
    db(
        """CREATE TABLE IF NOT EXISTS configs (
       courseCode varchar(128),
       config LONGBLOB)"""
    )
    db(
        """CREATE TABLE IF NOT EXISTS students (
       courseCode varchar(128),
       email varchar(128),
       shortData varchar(256),
       data BLOB)"""
    )
    db(
        """CREATE TABLE IF NOT EXISTS headers (
       courseCode varchar(128),
       header BLOB)"""
    )
    db(
        """CREATE TABLE IF NOT EXISTS lastUpdated (
       courseCode varchar(128),
       lastUpdated TIMESTAMP)"""
    )
    db(
        """CREATE TABLE IF NOT EXISTS regrade_requests (
        courseCode varchar(128),
        email varchar(128),
        assignment varchar(128),
        backup_id varchar(6),
        description varchar(255),
        status varchar(128),
        assigned_to varchar(128),
        resolution_reason varchar(255),
        emailed varchar(128)
        )"""
    )

if DEV and not IS_SPHINX:
    with connect_db() as db:
        with open("./public/config/dummy_grade_data.csv") as grades:
            set_grades(grades.read(), "cs61a", db)
        set_default_config(db)


def last_updated():
    """Finds the timestamp of when the current database was last updated
     for this course.

     Uses a database query function yielded by :func:`common.db.connect_db`
     and the course code returned by :func:`common.course_config.get_course`

    :return: Timestamp or ``Unknown`` (string) if any exceptions occur while fetching from the current database
    """
    try:
        with connect_db() as db:
            return db(
                "SELECT lastUpdated from lastUpdated where courseCode=%s",
                [get_course()],
            ).fetchone()[0]
    except:
        return "Unknown"


def create_client(app):
    @app.route("/")
    def index():
        return render_template("index.html", courseCode=get_course())

    @app.route("/histogram")
    def histogram():
        return render_template("index.html", courseCode=get_course())

    @app.route("/requests")
    def regrade_requests():
        return render_template("index.html", courseCode=get_course())

    @app.route("/redirect")
    def ohlord():
        return redirect("https://howamidoing.cs61a.org")

    @app.route("/edit")
    def config_editor():
        return render_template("index.html", courseCode=get_course())

    @app.route("/config/config.js")
    def config():
        with connect_db() as db:
            data = db(
                "SELECT config FROM configs WHERE courseCode=%s", [get_course()]
            ).fetchone()
            print(data)
            return Response(data, mimetype="application/javascript")

    @app.route("/submitRegradeRequest", methods=["GET", "POST"])
    def submitRegradeRequest():
        if not is_logged_in():
            return dict(success=False)
        if request.method == "GET":
            return dict(success=False)
        email = request.form.get("email")
        assignment = request.form.get("assignment")

        with connect_db() as db:
            status = db(
                "SELECT status FROM regrade_requests WHERE courseCode=%s AND email=%s AND assignment=%s",
                [get_course(), email, assignment],
            ).fetchone()
            if status:
                status = status[0]
        if status and status not in ("needs followup"):
            return dict(success=False)

        backup_id = request.form.get("backup_id")
        description = request.form.get("description")
        ta = request.form.get("ta")
        status = "requested"
        with connect_db() as db:
            db(
                """INSERT INTO regrade_requests (
                courseCode, email, assignment, backup_id, description, assigned_to, status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                [get_course(), email, assignment, backup_id, description, ta, status],
            )
        return redirect("/")

    @app.route("/getRegradeRequests")
    def getRegradeRequests():
        if not is_staff(get_course()):
            return dict(success=False)
        with connect_db() as db:
            if request.args.get("for", "me") == "all":
                regrade_requests = db(
                    "SELECT email, assignment, backup_id, description, status FROM regrade_requests"
                )
            else:
                regrade_requests = db(
                    "SELECT email, assignment, backup_id, description, status FROM regrade_requests WHERE assigned_to=%s",
                    [get_user()["email"]],
                )
            data = [
                dict(
                    email=row[0],
                    assignment=row[1],
                    backup_id=row[2],
                    description=row[3],
                    status=row[4],
                )
                for row in regrade_requests
            ]
            return jsonify(data)

    @app.route("/resolveRegradeRequest", methods=["GET", "POST"])
    def resolveRegradeRequest():
        if not is_staff(get_course()):
            return dict(success=False)
        if request.method == "GET":
            return dict(success=False)
        email = request.form.get("email")
        assignment = request.form.get("assignment")
        backup_id = request.form.get("backup_id")
        resolution = request.form.get("resolution").lower()
        reason = request.form.get("reason")
        email_preview = request.form.get("email_preview")
        with connect_db() as db:
            db(
                """UPDATE regrade_requests SET 
                status=%s, resolution_reason=%s, emailed=%s
                WHERE courseCode=%s AND email=%s AND assignment=%s AND backup_id=%s""",
                [resolution, reason, "yes", get_course(), email, assignment, backup_id],
            )
        return redirect("/")

    @app.route("/canRegrade")
    def canRequestRegrade():
        if not is_logged_in():
            return dict(canRegrade=False)
        email = request.args.get("email", "")
        assignment = request.args.get("name", "")
        with connect_db() as db:
            status = db(
                "SELECT status FROM regrade_requests WHERE courseCode=%s AND email=%s AND assignment=%s",
                [get_course(), email, assignment],
            ).fetchone()
            if status:
                status = status[0]
        return dict(canRegrade=(not status or status in ("needs followup")))

    @app.route("/query/")
    def query():
        try:
            if is_logged_in():
                user = get_user()

                email = user["email"]
                target = request.args.get("target", None)
                admin = True if DEV else is_admin(course=get_course(), email=email)

                if is_staff(get_course()):
                    if target:
                        email = target
                    else:
                        all_students = []
                        with connect_db() as db:
                            lookup = db(
                                "SELECT shortData FROM students WHERE courseCode=%s",
                                [get_course()],
                            ).fetchall()
                            for row in lookup:
                                parsed = json.loads(row[0])
                                if admin or parsed.get("TA", "") in ("", email):
                                    all_students.append(parsed)
                        return jsonify(
                            {
                                "success": True,
                                "isStaff": True,
                                "isAdmin": admin,
                                "allStudents": all_students,
                                "email": user["email"],
                                "name": user["name"],
                                "lastUpdated": last_updated(),
                            }
                        )

                with connect_db() as db:
                    [short_data, data] = db(
                        "SELECT shortData, data FROM students WHERE courseCode=%s AND email=%s",
                        [get_course(), email],
                    ).fetchone()
                    [header] = db(
                        "SELECT header FROM headers WHERE courseCode=%s", [get_course()]
                    ).fetchone()
                    short_data = json.loads(short_data)
                    if not (
                        email == user["email"]
                        or admin
                        or short_data.get("TA", "") in ("", user["email"])
                    ):
                        return jsonify({"success": False, "retry": False})
                    data = json.loads(data)
                    header = json.loads(header)
                    return jsonify(
                        {
                            "success": True,
                            "header": header,
                            "data": data,
                            "email": short_data["Email"],
                            "name": short_data["Name"],
                            "SID": short_data["SID"],
                            "ta": short_data["TA"],
                            "lastUpdated": last_updated(),
                        }
                    )
            else:
                return jsonify({"success": False, "retry": True})

        except Exception:
            pass
        return jsonify({"success": False, "retry": False})

    @app.route("/allScores", methods=["POST"])
    def all_scores():
        if not is_staff(get_course()):
            return jsonify({"success": False})
        with connect_db() as db:
            [header] = db(
                "SELECT header FROM headers WHERE courseCode=%s", [get_course()]
            ).fetchone()
            header = json.loads(header)
            data = db(
                "SELECT data FROM students WHERE courseCode=%s", get_course()
            ).fetchall()
            scores = []
            for [score] in data:
                score = json.loads(score)
                scores.append(score)
            return jsonify({"header": header, "scores": scores})

    @app.route("/setConfig", methods=["POST"])
    def set_config():
        if not is_staff(get_course()):
            return jsonify({"success": False})
        data = request.form.get("data")
        with connect_db() as db:
            db("DELETE FROM configs WHERE courseCode=%s", [get_course()])
            db("INSERT INTO configs VALUES (%s, %s)", [get_course(), data])
        return jsonify({"success": True})

    @app.route("/setGrades", methods=["POST"])
    def set_grades_route():
        if not is_staff(get_course()):
            return jsonify({"success": False})
        data = request.form.get("data")
        with transaction_db() as db:
            set_grades(data, get_course(), db)

        return jsonify({"success": True})

    @app.route("/setGradesSecret", methods=["POST"])
    def set_grades_secret_route():
        if validate_secret(secret=request.form.get("secret")) != "cs61a":
            return jsonify({"success": False})
        data = request.form.get("data")
        with transaction_db() as db:
            set_grades(data, get_course(), db)

        return jsonify({"success": True})

    @rpc_upload_grades.bind(app)
    @only("grade-display", allow_staging=True)
    def upload_grades(data: str):
        with transaction_db() as db:
            set_grades(data, get_course(), db)


def print_to_stderr(print_function):
    """Writes to sys.stderr using the desired print function.

    :param print_function: a print function

    :return: a function that writes the input to sys.stderr using the desired print function
    """

    def print(*s):
        print_function(*s, file=sys.stderr)

    return print


print = print_to_stderr(print)


app = Flask(
    __name__, static_url_path="", static_folder="static", template_folder="static"
)

if __name__ == "__main__":
    app.debug = True

create_client(app)
create_oauth_client(app, CONSUMER_KEY)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)

import re
import string
from random import SystemRandom

from flask import request, redirect, jsonify, render_template

from common.db import connect_db
from auth_utils import (
    key_secure,
    oauth_secure,
    admin_oauth_secure,
    course_oauth_secure,
    MASTER_COURSE,
    is_staff,
    get_name,
    get_user,
)
from common.rpc.auth import get_endpoint, get_endpoint_id, list_courses, validate_secret
from common.url_for import url_for
from common.html import html, make_row


def init_db():
    with connect_db() as db:
        db(
            """CREATE TABLE IF NOT EXISTS auth_keys (
                client_name varchar(128), 
                auth_key varchar(128),
                creator varchar(128),
                course varchar(128),
                service varchar(128),
                unused BOOLEAN
             )"""
        )
        db(
            """CREATE TABLE IF NOT EXISTS super_auth_keys (
                client_name varchar(128), 
                auth_key varchar(128),
                creator varchar(128),
                unused BOOLEAN
             )"""
        )
        db(
            """CREATE TABLE IF NOT EXISTS courses (
                course varchar(128),
                endpoint varchar(128),
                endpoint_id INTEGER
            )"""
        )
        ret = db("SELECT * FROM courses WHERE course=(%s)", [MASTER_COURSE]).fetchone()
        if not ret:
            db(
                "INSERT INTO courses (course, endpoint, endpoint_id) VALUES (%s, %s, %s)",
                ["cs61a", "cal/cs61a/sp20", 151],
            )


init_db()


def gen_key(length=64):
    return "".join(
        SystemRandom().choice(string.ascii_uppercase + string.digits)
        for _ in range(length)
    )


def prettify(course_code):
    m = re.match(r"([a-z]+)([0-9]+[a-z]?)", course_code)
    return m and (m.group(1) + " " + m.group(2)).upper()


class Data:
    def __init__(self):
        self.callbacks = []

    def add(self, callback):
        self.callbacks.append(callback)

    def render(self, *args):
        return "<p>".join(callback(*args) for callback in self.callbacks)


def create_management_client(app):
    app.general_info = Data()
    app.help_info = Data()

    def general_help():
        return """
            <title>61A Auth</title>
            <link rel="icon" href="https://cs61a.org/assets/images/favicon.ico">
            <h1 class="mt-5"> 61A Auth </h1>
            Go to <a href="https://go.cs61a.org/auth-help">go/auth-help</a> to see detailed usage / deployment instructions.
        """

    def superadmin():
        if not is_staff(MASTER_COURSE):
            return ""

        with connect_db() as db:
            courses = db(
                "SELECT course, endpoint FROM courses ORDER BY course"
            ).fetchall()
        with connect_db() as db:
            super_clients = db(
                "SELECT client_name, creator FROM super_auth_keys ORDER BY client_name"
            ).fetchall()

        return render_template(
            "admin.html",
            courses=[
                (
                    client,
                    endpoint,
                    make_row("", url_for("remove_course", course=client)),
                )
                for client, endpoint in courses
            ],
            super_clients=[
                (
                    name,
                    creator,
                    make_row("", url_for("revoke_super_key", client_name=name)),
                )
                for name, creator in super_clients
            ],
        )

    app.general_info.add(general_help)
    app.general_info.add(superadmin)

    def course_config(course):
        with connect_db() as db:
            endpoint, endpoint_id = db(
                "SELECT endpoint, endpoint_id FROM courses WHERE course=(%s)", [course]
            ).fetchone()

            user_data = get_user()
            for participation in user_data["participations"]:
                if participation["course"]["offering"] == endpoint:
                    endpoint_id = participation["course_id"]

            db(
                "UPDATE courses SET endpoint_id=(%s) WHERE endpoint=(%s)",
                [[endpoint_id, endpoint]],
            )

            return """
                <h3>Config</h3>
                <p>
                Current endpoint: {} (id: {})
                </p>
                Set new endpoint:
                <form action="/api/{}/set_endpoint" method="post">
                    <input name="endpoint" type="text" placeholder="OKPy endpoint">
                    <input type="submit">
                </form>
            """.format(
                endpoint, endpoint_id, course
            )

    app.help_info.add(lambda course: "<p></p><h2>{}</h2>".format(prettify(course)))
    app.help_info.add(course_config)

    @app.route("/")
    @oauth_secure()
    def index():
        out = [app.general_info.render()]
        with connect_db() as db:
            for course, endpoint in db(
                "SELECT course, endpoint FROM courses"
            ).fetchall():
                if is_staff(course):
                    out.append(app.help_info.render(course))
        return html("".join(out))

    @app.route("/api/add_course", methods=["POST"])
    @admin_oauth_secure(app)
    def add_course():
        course = request.form["course"]
        endpoint = request.form["endpoint"]
        if not prettify(course):
            return (
                "Course code not formatted correctly. It should be lowercase with no spaces.",
                400,
            )
        with connect_db() as db:
            ret = db("SELECT * FROM courses WHERE course = (%s)", course).fetchone()
            if ret:
                return "A course already exists with the same name.", 403
            db("INSERT INTO courses VALUES (%s, %s, %s)", [course, endpoint, None])
        return redirect("/")

    @app.route("/api/remove_course", methods=["POST"])
    @admin_oauth_secure(app)
    def remove_course():
        course = request.args["course"]
        with connect_db() as db:
            db("DELETE FROM courses WHERE course = (%s)", [course])
        return redirect("/")

    @list_courses.bind(app)
    def handle_list_courses(**_kwargs):
        # note: deliberately not secured, not sensitive data
        with connect_db() as db:
            return [
                list(x) for x in db("SELECT course, endpoint FROM courses").fetchall()
            ]

    # noinspection PyPep8Naming
    @app.route("/api/<course>/get_endpoint", methods=["POST"])
    def handle_get_endpoint_DEPRECATED_DO_NOT_USE(course):
        return jsonify(handle_get_endpoint(course))

    @get_endpoint.bind(app)
    def handle_get_endpoint(course):
        # note: deliberately not secured, not sensitive data
        with connect_db() as db:
            endpoint = db(
                "SELECT endpoint FROM courses WHERE course = (%s)", [course]
            ).fetchone()
        if endpoint:
            return endpoint[0]
        raise KeyError

    @validate_secret.bind(app)
    @key_secure
    def handle_validate_secret(course):
        return course

    @app.route("/api/<course>/set_endpoint", methods=["POST"])
    @course_oauth_secure()
    def set_endpoint(course):
        endpoint = request.form["endpoint"]
        with connect_db() as db:
            db(
                "UPDATE courses SET endpoint = (%s) WHERE course = (%s)",
                [endpoint, course],
            )
        return redirect("/")

    # noinspection PyPep8Naming
    @app.route("/api/<course>/get_endpoint_id", methods=["POST"])
    def handle_get_endpoint_id_DEPRECATED_DO_NOT_USE(course):
        return jsonify(handle_get_endpoint_id(course))

    @get_endpoint_id.bind(app)
    def handle_get_endpoint_id(course):
        with connect_db() as db:
            endpoint = db(
                "SELECT endpoint_id FROM courses WHERE course = (%s)", [course]
            ).fetchone()
        if endpoint:
            return endpoint[0]

    @app.route("/api/request_super_key", methods=["POST"])
    @admin_oauth_secure(app)
    def create_super_key():
        name = request.form["client_name"]
        key = gen_key()
        with connect_db() as db:
            ret = db(
                "SELECT * FROM auth_keys WHERE client_name = (%s)", [name]
            ).fetchone()
            if ret:
                return "client_name already in use", 409
            ret = db(
                "SELECT * FROM super_auth_keys WHERE client_name = (%s)", [name]
            ).fetchone()
            if ret:
                return "client_name already in use", 409
            db(
                "INSERT INTO super_auth_keys VALUES (%s, %s, %s, %s)",
                [name, key, get_name(), True],
            )
        return key

    @app.route("/api/revoke_super_key", methods=["POST"])
    @admin_oauth_secure(app)
    def revoke_super_key():
        name = request.args["client_name"]
        with connect_db() as db:
            db("DELETE FROM super_auth_keys WHERE client_name = (%s)", [name])
        return redirect("/")

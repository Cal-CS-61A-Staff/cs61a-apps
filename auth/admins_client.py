from flask import redirect, request

from auth_utils import course_oauth_secure, get_name, key_secure, get_email
from common.db import connect_db
from common.rpc.auth import is_admin, list_admins, user_can, read_spreadsheet
from common.url_for import url_for
from common.html import error, make_row

import json


def init_db():
    with connect_db() as db:
        db(
            """CREATE TABLE IF NOT EXISTS course_admins (
                email varchar(128), 
                name varchar(128), 
                course varchar(128),
                creator varchar(128)
             )"""
        )
        db(
            """CREATE TABLE IF NOT EXISTS course_permissions (
                course varchar(128),
                url varchar(256),
                sheet varchar(128)
            )"""
        )


init_db()


def create_admins_client(app):
    def admin_data(course):
        with connect_db() as db:
            ret = db(
                "SELECT email, name, course, creator FROM course_admins WHERE course=(%s)",
                [course],
            ).fetchall()
        admin_names = [
            make_row(
                f'{name} (<a href="mailto:{email}">{email}</a>), added by {creator} ',
                url_for("remove_admin", course=course, email=email),
            )
            for email, name, course, creator in ret
        ]
        add_admin = f"""
            Add new course administrator:
            <form action="{url_for("add_admin", course=course)}" method="post">
                <input name="email" type="email" placeholder="Email address">
                <input type="submit">
            </form>
        """
        with connect_db() as db:
            ret = db(
                "SELECT url, sheet FROM course_permissions WHERE course=(%s)", [course]
            ).fetchall()
        perms_sheet = [
            make_row(
                f'<a href="{url}">{sheet} ({url})</a>',
                url_for("unset_granular_spreadsheet", course=course),
            )
            for url, sheet in ret
        ]  # there should only be 0-1 perms sheets
        add_perms_sheet = f"""
            Add granular permissions sheet (first column should be email, the rest should be permission names):
            <form action="{url_for("set_granular_spreadsheet", course=course)}" method="post">
                <input name="url" placeholder="URL">
                <input name="sheet" placeholder="Sheet Name">
                <input type="submit">
            </form>
        """
        return (
            "<h3>Admins</h3>"
            + add_admin
            + "<p>".join(admin_names)
            + "<br>"
            + "<h3>Granular Permissions</h3>"
            + add_perms_sheet
            + "<p>".join(perms_sheet)
        )

    app.help_info.add(admin_data)

    @app.route("/admins/<course>/add_admin", methods=["POST"])
    @course_oauth_secure()
    def add_admin(course):
        email = request.form["email"]
        with connect_db() as db:
            check = db(
                "SELECT * FROM course_admins WHERE email=(%s) AND course=(%s)",
                [email, course],
            ).fetchone()
        if check:
            return error("User is already an admin"), 409
        with connect_db() as db:
            db(
                "INSERT INTO course_admins VALUES (%s, %s, %s, %s)",
                [email, "Unknown", course, get_name()],
            )

        # make sure that you can't accidentally lock yourself out
        with connect_db() as db:
            check = db(
                "SELECT * FROM course_admins WHERE email=(%s) AND course=(%s)",
                [get_email(), course],
            ).fetchone()
            if not check:
                db(
                    "INSERT INTO course_admins VALUES (%s, %s, %s, %s)",
                    [get_email(), get_name(), course, get_name()],
                )

        return redirect(url_for("index"))

    @app.route("/admins/<course>/remove_admin", methods=["POST"])
    @course_oauth_secure()
    def remove_admin(course):
        email = request.args["email"]
        with connect_db() as db:
            db(
                "DELETE FROM course_admins WHERE email=(%s) AND course=(%s)",
                [email, course],
            )
        return redirect(url_for("index"))

    @app.route("/admins/<course>/set_granular_spreadsheet", methods=["POST"])
    @course_oauth_secure()
    def set_granular_spreadsheet(course):
        url = request.form["url"]
        sheet = request.form["sheet"]
        with connect_db() as db:
            db("DELETE FROM course_permissions WHERE course=(%s)", [course])
            db(
                "INSERT INTO course_permissions (course, url, sheet) VALUES (%s, %s, %s)",
                [course, url, sheet],
            )
        return redirect(url_for("index"))

    @app.route("/admins/<course>/unset_granular_spreadsheet", methods=["POST"])
    @course_oauth_secure()
    def unset_granular_spreadsheet(course):
        with connect_db() as db:
            db("DELETE FROM course_permissions WHERE course=(%s)", [course])
        return redirect(url_for("index"))

    @is_admin.bind(app)
    @key_secure
    def handle_is_admin(course, email, force_course=None):
        if force_course and course != force_course:
            raise PermissionError
        with connect_db() as db:
            return bool(
                db(
                    "SELECT * FROM course_admins WHERE email=(%s) AND course=(%s)",
                    [email, force_course if force_course else course],
                ).fetchone()
            )

    @list_admins.bind(app)
    @key_secure
    def handle_list_admins(course):
        with connect_db() as db:
            return [
                list(x)
                for x in db(
                    "SELECT email, name FROM course_admins WHERE course=(%s)", [course]
                ).fetchall()
            ]

    @user_can.bind(app)
    @key_secure
    def handle_user_can(course, email, action):
        if is_admin(course, email):
            return True

        with connect_db() as db:
            [url, sheet] = db(
                "SELECT url, sheet FROM course_permissions WHERE course=(%s)", [course]
            ).fetchone()
            if not url:
                return False

        data = web_json(url=url, sheet_name=sheet)
        return action in data[email]


def web_json(url, sheet):
    resp = read_spreadsheet(url=url, sheet_name=sheet)
    data = {}
    for row in resp[1:]:
        email, perms = row[0], row[1:]
        data[email] = perms
    return data

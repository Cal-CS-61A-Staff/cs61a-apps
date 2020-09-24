import re
import string
from random import SystemRandom

from flask import redirect, request

from auth_utils import admin_oauth_secure, course_oauth_secure, get_name
from common.db import connect_db
from common.url_for import url_for
from html_utils import make_row


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


init_db()


def gen_key(length=64):
    return "".join(
        SystemRandom().choice(string.ascii_uppercase + string.digits)
        for _ in range(length)
    )


def prettify(course_code):
    m = re.match(r"([a-z]+)([0-9]+[a-z]?)", course_code)
    return m and (m.group(1) + " " + m.group(2)).upper()


def create_auth_client(app):
    def client_data(course):
        with connect_db() as db:
            ret = db(
                "SELECT client_name, creator, unused FROM auth_keys WHERE course=(%s)",
                [course],
            ).fetchall()
        client_names = [
            make_row(
                f'{client_name}, created by {creator} {"(unused)" if unused else ""} ',
                url_for("revoke_key", course=course, client_name=client_name),
            )
            for client_name, creator, unused in ret
        ]
        create_client = f"""
            Create new client and obtain secret key:
            <form action="{url_for("create_key", course=course)}" method="post">
                <input name="client_name" type="text" placeholder="client_name">
                <input type="submit">
            </form>
        """
        return "<h3>Clients</h3>" + create_client + "".join(client_names)

    app.help_info.add(client_data)

    @app.route("/auth/<course>/request_key", methods=["POST"])
    @course_oauth_secure()
    def create_key(course):
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
                "INSERT INTO auth_keys VALUES (%s, %s, %s, %s, %s, %s)",
                [name, key, get_name(), course, "all", True],
            )
        return key

    @app.route("/auth/<course>/revoke_key", methods=["POST"])
    @course_oauth_secure()
    def revoke_key(course):
        name = request.args["client_name"]
        with connect_db() as db:
            db(
                "DELETE FROM auth_keys WHERE client_name = (%s) and course = (%s)",
                [name, course],
            )
        return redirect("/")

    @app.route("/auth/<course>/revoke_all_unused_keys", methods=["POST"])
    @course_oauth_secure()
    def revoke_all_unused_keys(course):
        with connect_db() as db:
            db("DELETE FROM auth_keys WHERE unused = TRUE and course = (%s)", [course])
        return "All unused keys revoked."

    @app.route("/auth/DANGEROUS_revoke_all_keys", methods=["POST"])
    @admin_oauth_secure(app)
    def revoke_all_keys():
        with connect_db() as db:
            db("DROP TABLE auth_keys")
            init_db()
        return "ALL keys revoked. Any tools depending on 61A Auth will no longer work."

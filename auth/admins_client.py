from flask import redirect, request

from auth_utils import course_oauth_secure, get_name, key_secure, get_email
from common.db import connect_db
from common.rpc.auth import is_admin, list_admins
from common.url_for import url_for
from common.html import error, make_row


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


init_db()


def create_admins_client(app):
    def client_data(course):
        with connect_db() as db:
            ret = db(
                "SELECT email, name, course, creator FROM course_admins WHERE course=(%s)",
                [course],
            ).fetchall()
        admin_names = [
            "<td>{}</td><td>{}</td><td>".format(
                f'<a href="mailto:{email}">{email}</a>', creator
            )
            + make_row(
                "",  # f'{name} (<a href="mailto:{email}">{email}</a>), added by {creator} ',
                url_for("remove_admin", course=course, email=email),
            )
            + "</td>"
            for email, name, course, creator in ret
        ]
        create_client = f"""
            Add new course administrator:
            <form action="{url_for("add_admin", course=course)}" method="post">
                <input name="email" type="email" placeholder="Email address">
                <input type="submit">
            </form>
        """
        return (
            "<h3>Admins</h3>"
            + create_client
            + """
            <table>
                <tbody>
                    <tr>
                        <th>Email</th>
                        <th>Added By</th>
                        <th>Remove</th>
                    </tr>
        """
            + "".join("<tr>" + a + "</tr>" for a in admin_names)
            + "</tbody></table>"
        )

    app.help_info.add(client_data)

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

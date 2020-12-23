from flask import request, jsonify, redirect
from piazza_api import Piazza

from auth_utils import key_secure, course_oauth_secure
from common.db import connect_db
from common.html import html
from common.rpc.auth import perform_piazza_action, piazza_course_id


def init_db():
    with connect_db() as db:
        db(
            """CREATE TABLE IF NOT EXISTS piazza_config (
                course_id varchar(256),
                test_course_id varchar(256),
                student_user varchar(256),
                student_pw varchar(256),
                staff_user varchar(256),
                staff_pw varchar(256),
                course varchar(128)
            )"""
        )


init_db()


def create_piazza_client(app):
    def piazza_help(course):
        with connect_db() as db:
            ret = db(
                "SELECT student_user, staff_user, course_id, test_course_id FROM piazza_config WHERE course=%s",
                [course],
            ).fetchone()
            student_email, staff_email, course_id, test_course_id = (
                ret if ret else [""] * 4
            )
        return f"""
        <h3> Piazza Service Accounts </h3>
        Student email address: <a href="mailto:{student_email}">{student_email}</a>
        <p>
        Staff email address: <a href="mailto:{staff_email}">{staff_email}</a>
        <p>
        Piazza course: <a href="https://piazza.com/class/{course_id}">https://piazza.com/class/{course_id}</a>
        <p>
        Test Piazza course: <a href="https://piazza.com/class/{test_course_id}">https://piazza.com/class/{test_course_id}</a>
        <p>
        Enroll these accounts on the latest course Piazza.
        <p>
        To configure, go to <a href="/piazza/{course}/config">Piazza Config</a>.
        """

    app.help_info.add(piazza_help)

    # noinspection PyPep8Naming
    @app.route("/piazza/<action>", methods=["POST"])
    def perform_action_DEPRECATED_DO_NOT_USE(action):
        kwargs = dict(request.json)
        del kwargs["client_name"]
        is_test = kwargs.pop("test", False)
        as_staff = kwargs.pop("staff")
        secret = kwargs.pop("secret")
        course = kwargs.pop("course", None)
        kwargs.pop("test", None)
        return jsonify(
            perform_action(
                secret=secret,
                course=course,
                action=action,
                as_staff=as_staff,
                is_test=is_test,
                kwargs=kwargs,
            )
        )

    @perform_piazza_action.bind(app)
    @key_secure
    def perform_action(action, course, as_staff=False, is_test=None, kwargs=None):
        with connect_db() as db:
            if as_staff:
                user, pw = db(
                    "SELECT staff_user, staff_pw FROM piazza_config WHERE course = (%s)",
                    [course],
                ).fetchone()
            else:
                user, pw = db(
                    "SELECT student_user, student_pw FROM piazza_config WHERE course = (%s)",
                    [course],
                ).fetchone()
            if is_test:
                (course_id,) = db(
                    "SELECT test_course_id FROM piazza_config WHERE course = (%s)",
                    [course],
                ).fetchone()
            else:
                (course_id,) = db(
                    "SELECT course_id FROM piazza_config WHERE course = (%s)", [course]
                ).fetchone()

        p = Piazza()
        p.user_login(user, pw)
        course = p.network(course_id)
        if kwargs is None:
            kwargs = {}
        try:
            return getattr(course, action)(**kwargs)
        except Exception as e:
            return str(e), 400

    # noinspection PyUnusedLocal `staff` exists only for API backwards compatibility
    @piazza_course_id.bind(app)
    @key_secure
    def course_id(course, staff=False, test=False, is_test=False):
        is_test = test or is_test  # test exists for backwards compatibility only
        with connect_db() as db:
            if is_test:
                (course_id,) = db(
                    "SELECT test_course_id FROM piazza_config WHERE course=(%s)",
                    [course],
                ).fetchone()
            else:
                (course_id,) = db(
                    "SELECT course_id FROM piazza_config WHERE course=(%s)", [course]
                ).fetchone()
        return course_id

    @app.route("/piazza/<course>/config", methods=["GET"])
    @course_oauth_secure()
    def piazza_config(course):
        return html(
            f"""
            Enter account details for Piazza service accounts. Leave fields blank to avoid updating them.
            Ensure that these accounts are enrolled in the appropriate Piazzas!
            <form action="/piazza/{course}/set_config" method="post">
                <label>
                    Piazza course ID <br />
                    <input name="course_id" type="text"> <br />
                </label>
                <label>
                    Test Piazza course ID <br />
                    <input name="test_course_id" type="text"> <br />
                </label>
                <br />
                <label>
                    Student Username <br />
                    <input name="student_user" type="text"> <br />
                </label>
                <label>
                    Student Password <br />
                    <input name="student_pw" type="password"> <br />
                </label>
                <br />
                <label>
                    Staff Username <br />
                    <input name="staff_user" type="text"> <br />
                </label>
                <label>
                    Staff Password <br />
                    <input name="staff_pw" type="password"> <br />
                </label>
                <label>
                <input type="submit">
            </form>
        """
        )

    @app.route("/piazza/<course>/set_config", methods=["POST"])
    @course_oauth_secure()
    def set_piazza_config(course):
        with connect_db() as db:
            ret = db(
                "SELECT * FROM piazza_config WHERE course=(%s)", [course]
            ).fetchone()
            if ret:
                (
                    course_id,
                    test_course_id,
                    student_user,
                    student_pw,
                    staff_user,
                    staff_pw,
                    _,
                ) = ret
            else:
                (
                    course_id,
                    test_course_id,
                    student_user,
                    student_pw,
                    staff_user,
                    staff_pw,
                ) = [""] * 6

        course_id = request.form["course_id"] or course_id
        test_course_id = request.form["test_course_id"] or test_course_id
        student_user = request.form["student_user"] or student_user
        student_pw = request.form["student_pw"] or student_pw
        staff_user = request.form["staff_user"] or staff_user
        staff_pw = request.form["staff_pw"] or staff_pw

        with connect_db() as db:
            db("DELETE FROM piazza_config WHERE course=(%s)", [course])
            db(
                "INSERT INTO piazza_config VALUES (%s, %s, %s, %s, %s, %s, %s)",
                [
                    course_id,
                    test_course_id,
                    student_user,
                    student_pw,
                    staff_user,
                    staff_pw,
                    course,
                ],
            )
        return redirect("/")

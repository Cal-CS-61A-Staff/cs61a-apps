import json

from flask import request, url_for, abort
from werkzeug.utils import redirect

from common.rpc.auth import get_endpoint, list_courses, slack_workspace_name
from common.rpc.secrets import get_secret
from common.db import connect_db
from security import logged_in, get_staff_endpoints

REJECTED = object()
UNABLE = object()

CLIENT_ID = get_secret(secret_name="CLIENT_ID")


def get_add_to_slack_link(domain):
    return f"https://{domain}.slack.com/oauth/v2/authorize?client_id={CLIENT_ID}&scope=channels:join,channels:read,chat:write,users:read,users:read.email,groups:read&user_scope=channels:history,chat:write,groups:history,im:history,mpim:history,users:read"


with open("config.json") as f:
    CONFIG = json.load(f)


def init_db():
    with connect_db() as db:
        db(
            """CREATE TABLE IF NOT EXISTS tokens (
        user varchar(128),
        token text,
        PRIMARY KEY (`user`)
    );"""
        )

        db(
            """CREATE TABLE IF NOT EXISTS silenced_users (
                user varchar(128),            
                PRIMARY KEY (`user`)       
            );"""
        )

        db(
            """CREATE TABLE IF NOT EXISTS bot_data (
                bot_access_token varchar(256),
                team_id varchar(256),
                course varchar(128)
            )"""
        )

        db(
            """CREATE TABLE IF NOT EXISTS activated_services (
                course varchar(128),
                service varchar(128)
            )"""
        )


init_db()


def create_config_client(app):
    @app.route("/")
    @logged_in
    def index():
        staff_endpoints = set(get_staff_endpoints())
        active_courses = []
        for course, endpoint in list_courses():
            if endpoint in staff_endpoints:
                active_courses.append(course)

        if len(active_courses) == 0:
            return (
                "You are not a member of staff in any course that uses this tool",
                401,
            )
        if len(active_courses) == 1:
            return redirect(url_for("register_course", course=active_courses[0]))

        options = "<p>".join(
            '<button formaction="register/{}">{}</button>'.format(course, course)
            for course in active_courses
        )

        return f"""
            Please select your course:
            <form method="get">
                {options}
            </form>
        """

    @app.route("/register/<course>")
    def register_course(course):
        if get_endpoint(course=course) not in get_staff_endpoints():
            abort(403)

        with connect_db() as db:
            ret = db("SELECT * FROM bot_data WHERE course = (%s)", [course]).fetchone()

        if ret:
            # course already setup
            return redirect(get_add_to_slack_link(slack_workspace_name(course=course)))
        else:
            return redirect(url_for("course_config", course=course))

    @app.route("/config/<course>")
    def course_config(course):
        if get_endpoint(course=course) not in get_staff_endpoints():
            abort(403)

        with connect_db() as db:
            ret = db(
                "SELECT service FROM activated_services WHERE course = (%s)", [course]
            )
            active_services = set(x[0] for x in ret)

        service_list = "<br />".join(
            f"""
            <label>
                <input 
                    type="checkbox" 
                    name="{service}" 
                    {"checked" if service in active_services else ""}
                >
                {service.title()}: {description}
            </label>
        """
            for service, description in CONFIG["services"].items()
        )

        return f"""
            First, ensure that <a href="https://auth.apps.cs61a.org">61A Auth</a> is set up for your course.
            <p>
            Then set up the bot.
            <form action="{url_for("set_course_config", course=course)}" method="post">
                 Services:
                 <br />
                 {service_list}
                 <br />
                <input type="submit" />
            </form>
            <p>
            Then, <a href={get_add_to_slack_link(slack_workspace_name(course=course))}>
                add the slackbot to your workspace!
            </a>
        """

    @app.route("/set_config/<course>", methods=["POST"])
    def set_course_config(course):
        if get_endpoint(course=course) not in get_staff_endpoints():
            abort(403)

        with connect_db() as db:
            for service in CONFIG["services"]:
                db(
                    "DELETE FROM activated_services WHERE course=(%s) AND service=(%s)",
                    [course, service],
                )
                if service in request.form:
                    db(
                        "INSERT INTO activated_services VALUES (%s, %s)",
                        [course, service],
                    )

        return redirect(url_for("course_config", course=course))


def store_user_token(user, token):
    with connect_db() as db:
        result = db("SELECT user FROM tokens WHERE user=%s", (user,))
        if not result.fetchone():
            db("INSERT INTO tokens VALUES (%s, %s)", (user, token))
        db("UPDATE tokens SET token=(%s) WHERE user=(%s)", (token, user))


def get_user_token(user):
    with connect_db() as db:
        out = db("SELECT token FROM tokens WHERE user=%s", (user,)).fetchone()
        if not out:
            check = db(
                "SELECT user FROM silenced_users WHERE user=%s", (user,)
            ).fetchone()
            if check:  # user doesn't want to use the tool :(
                return REJECTED
            return UNABLE
        return out["token"]


def store_bot_token(course, team_id, token):
    with connect_db() as db:
        check = db("SELECT * FROM bot_data WHERE course = (%s)", [course]).fetchone()
        if not check:
            db("INSERT INTO bot_data VALUES (%s, %s, %s)", ["", "", course])

        db(
            "UPDATE bot_data SET bot_access_token=(%s), team_id=(%s) WHERE course=(%s)",
            [token, team_id, course],
        )


def get_team_data(team_id):
    with connect_db() as db:
        return db(
            "SELECT course, bot_access_token FROM bot_data WHERE team_id = (%s)",
            [team_id],
        ).fetchone()

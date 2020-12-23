import socket
from enum import Enum
from time import sleep

import requests
from flask import Flask, abort, redirect, request

from common.course_config import format_coursecode, is_admin
from common.db import connect_db
from common.html import html
from common.oauth_client import create_oauth_client, get_user, is_logged_in
from common.rpc.buildserver import get_base_hostname
from common.rpc.secrets import get_secret, validates_master_secret
from common.url_for import url_for
from common.rpc.domains import add_domain

APP_LOOKUP = {
    "oh": "oh",
    "hwparty": "oh",
    "joinme": "oh",
    "lab": "oh",
    "howamidoing": "howamidoing",
    "status": "howamidoing",
    "seating": "seating",
    "links": "shortlinks",
    "go": "shortlinks",
    # legacy prefixes
    "me100": "oh",
    "csenrolltest": "oh",
    "cs169-oh": "oh",
    "cs188-oh": "oh",
    "cs186-oh": "oh",
    "stat140-oh": "oh",
}


class Status(Enum):
    VALIDATING = "VALIDATING"
    DNS_INVALID = "DNS_INVALID"
    PROVISIONING = "PROVISIONING"
    PROVISIONING_FAILED = "PROVISIONING_FAILED"
    UPDATING_OAUTH = "UPDATING_OAUTH"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SUCCESS = "SUCCESS"


app = Flask(__name__, static_folder="", static_url_path="")
if __name__ == "__main__":
    app.debug = True

create_oauth_client(app, "61a-domains")


with connect_db() as db:
    db(
        """CREATE TABLE IF NOT EXISTS hosted_apps (
    domain VARCHAR(128),
    course VARCHAR(128),
    app VARCHAR(128),
    status VARCHAR(128)
)
"""
    )


@app.route("/")
def index():
    if not is_logged_in():
        return redirect(url_for("login"))
    return html(
        """
    Select course: 
    <form method="post" action="/view_course">
        <input placeholder="cs61a" name="course"> <input type="submit" value="Login">
    </form>"""
    )


@app.route("/view_course", methods=["POST"])
@app.route("/view_course/<course>", methods=["GET"], endpoint="canonical_view_course")
def view_course(course=None):
    if not course:
        course = request.form["course"]
        return redirect(url_for("canonical_view_course", course=course))
    if not is_logged_in():
        return redirect(url_for("login"))
    email = get_user()["email"]
    if not is_admin(email, course):
        abort(403)

    with connect_db() as db:
        apps = db(
            "SELECT domain, app, status FROM hosted_apps WHERE course=(%s)", [course]
        ).fetchall()

    return html(
        f"""
        <h2>Hosted Apps for {format_coursecode(course)}</h2>
        {"<p>".join(f"<code>{domain}</code> ({app}) - {status}" for domain, app, status in apps)}
    """
    )


def set_status(domain: str, status: Status):
    with connect_db() as db:
        db(
            "UPDATE hosted_apps SET status=(%s) WHERE domain=(%s)",
            [status.value, domain],
        )


@add_domain.bind(app)
@validates_master_secret
def add_domain(app, is_staging, course, domain):
    try:
        if app != "auth":
            abort(401)

        app = APP_LOOKUP[domain.split(".")[0]]

        with connect_db() as db:
            status = db(
                "SELECT status FROM hosted_apps WHERE domain=(%s)", [domain]
            ).fetchone()
            if status is not None and status[0] == Status.SUCCESS:
                return ""  # domain already provisioned
            db("DELETE FROM hosted_apps WHERE domain=(%s)", [domain])

        with connect_db() as db:
            db(
                "INSERT INTO hosted_apps (domain, course, app, status) VALUES (%s, %s, %s, %s)",
                [domain, course, app, Status.VALIDATING.value],
            )

        try:
            ip = socket.gethostbyname(domain)
        except socket.gaierror:
            ip = None
        if ip != socket.gethostbyname("proxy.cs61a.org"):
            set_status(domain, Status.DNS_INVALID)
            return

        set_status(domain, Status.PROVISIONING)

        try:
            requests.post(
                "https://proxy.cs61a.org/create_domain",
                json=dict(
                    app=app,
                    domain=domain,
                    target=get_base_hostname(target_app=app),
                    secret=get_secret(secret_name="DOMAIN_WEBHOOK_SECRET"),
                ),
            ).raise_for_status()
        except requests.exceptions.ConnectionError:
            pass  # nginx restarts so the connection crashes

        sleep(5)

        if not requests.get(f"https://{domain}/").ok:
            set_status(domain, Status.PROVISIONING_FAILED)
            return

        set_status(domain, Status.UPDATING_OAUTH)
        # TODO
        set_status(domain, Status.SUCCESS)
        return
    except:
        set_status(domain, Status.INTERNAL_ERROR)
        raise


if __name__ == "__main__":
    app.run(debug=True)

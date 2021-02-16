from html import escape
from json import loads

from flask import Flask, abort

from common.oauth_client import create_oauth_client, get_user, is_staff, login
from common.shell_utils import sh
from common.url_for import url_for
from common.rpc.auth import is_admin

app = Flask(__name__, static_folder="", static_url_path="")
if __name__ == "__main__":
    app.debug = True


create_oauth_client(app, "61a-logs")


@app.route("/")
def index():
    if not is_staff("cs61a"):
        return login()
    email = get_user()["email"]
    if not is_admin(course="cs61a", email=email):
        abort(401)

    service_list = "\n".join(
        f"<p /><a href={url_for('create_secret', service=service)}>{service}</a>"
        for service in list_services()
    )

    return f"""
    <h1>Log Viewer</h1>
    {service_list}
    """


@app.route("/service/<service>")
def create_secret(service):
    if not is_staff("cs61a"):
        return login()
    email = get_user()["email"]
    if not is_admin(course="cs61a", email=email):
        abort(401)

    if service not in list_services():
        abort(404)

    out = reversed(
        [
            entry["timestamp"] + " " + escape(entry["textPayload"])
            for entry in loads(
                sh(
                    "gcloud",
                    "logging",
                    "read",
                    f"projects/cs61a-140900/logs/run.googleapis.com AND resource.labels.service_name={service}",
                    "--limit",
                    "100",
                    "--format",
                    "json",
                    capture_output=True,
                )
            )
            if "textPayload" in entry
        ]
    )

    return "<pre>" + "\n".join(map(str, out)) + "</pre>"


def list_services():
    return [
        service["metadata"]["name"]
        for service in loads(
            sh(
                "gcloud",
                "run",
                "services",
                "list",
                "--platform",
                "managed",
                "--region",
                "us-west1",
                "--format",
                "json",
                "-q",
                capture_output=True,
            )
        )
    ]


if __name__ == "__main__":
    app.run(debug=True)

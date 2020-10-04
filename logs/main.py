from json import loads

from flask import Flask, redirect, url_for

from common.oauth_client import create_oauth_client, is_staff
from common.shell_utils import sh

app = Flask(__name__, static_folder="", static_url_path="")
if __name__ == "__main__":
    app.debug = True


create_oauth_client(app, "61a-logs")


@app.route("/")
def index():
    if not is_staff("cs61a"):
        return redirect(url_for("login"))
    return """
    <h1>Log Viewer</h1>
    """


@app.route("/service/<service>")
def create_secret(service):
    if not is_staff("cs61a"):
        return redirect(url_for("login"))

    out = [
        entry["textPayload"]
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

    return "<pre>" + "\n".join(map(str, out)) + "</pre>"


if __name__ == "__main__":
    app.run(debug=True)

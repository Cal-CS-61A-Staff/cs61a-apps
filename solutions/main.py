from flask import Flask, redirect
from flask_compress import Compress
from static_server.utils import get_bucket, serve_path

from common.oauth_client import (
    create_oauth_client,
    is_enrolled,
    login,
    get_user,
    AUTHORIZED_ROLES,
)
from common.course_config import get_endpoint

app = Flask(__name__)
if __name__ == "__main__":
    app.debug = True


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>", methods=["GET"])
def index(path):
    try:
        info = get_user()
        for p in info["participations"]:
            if (
                p["course"]["offering"] == get_endpoint("cs61a")
                and p["role"] == "student"
            ):
                return redirect("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    except:
        pass  # don't let the rickroll crash anything else

    if not is_enrolled("cs61a", roles=[*AUTHORIZED_ROLES, "lab assistant"]):
        return login()
    bucket = get_bucket(
        {
            "cs61a": "website-base",
            "solutions2": "website-base",
            "solutions": "website-base",
        },
        "website-base",
    )
    return serve_path(bucket, "/unreleased/", path, path_404="404/index.html")


Compress(app)
create_oauth_client(app, "cs61a-staging")

if __name__ == "__main__":
    app.run(debug=True)

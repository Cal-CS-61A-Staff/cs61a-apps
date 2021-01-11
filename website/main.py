from flask import Flask
from flask_compress import Compress
from static_server.utils import get_bucket, serve_path

from common.oauth_client import create_oauth_client, is_staff, login
from common.url_for import get_host

app = Flask(__name__)
if __name__ == "__main__":
    app.debug = True


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>", methods=["GET"])
def index(path):
    if ".pr." in get_host() and not is_staff("cs61a"):
        return login()

    bucket = get_bucket(
        {
            "cs61a": "website-base",
            "website": "website-base",
            "website-server": "website-base",
        },
        "website-base",
    )
    return serve_path(bucket, "/released/", path, path_404="404/")


Compress(app)
create_oauth_client(app, "cs61a-staging")


if __name__ == "__main__":
    app.run(debug=True)

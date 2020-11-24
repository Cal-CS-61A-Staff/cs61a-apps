from flask import Flask, redirect
from flask_compress import Compress

from static_server.utils import get_bucket, serve_path

app = Flask(__name__)
if __name__ == "__main__":
    app.debug = True


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>", methods=["GET"])
def index(path):
    bucket = get_bucket(
        {
            "wiki": "wiki-base",
        },
        "wiki-base",
    )
    return serve_path(bucket, "/", path)


Compress(app)


if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask
from flask_compress import Compress

from utils import get_bucket, serve_path

app = Flask(__name__, static_folder=None)
if __name__ == "__main__":
    app.debug = True


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>", methods=["GET"])
def get(path):
    bucket = get_bucket(
        {
            "time": "time",
            "loom": "loom",
            "react": "react",
            "ok-help": "ok-help",
            "wiki": "wiki",
            "docs": "docs",
            "cs170-website": "cs170-website",
            "cs170": "cs170-website",
            # simple default app for PR testing
            "static-server": "time",
        },
        "time",
    )
    return serve_path(bucket, "/", path)


Compress(app)


if __name__ == "__main__":
    app.run(debug=True)

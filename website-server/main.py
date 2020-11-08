from flask import Flask
from flask_compress import Compress

from utils import get_bucket, serve_path

app = Flask(__name__)
if __name__ == "__main__":
    app.debug = True


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>", methods=["GET"])
def get(path):
    bucket = get_bucket({"cs61a": "website", "website-server": "website"}, "website")
    return serve_path(bucket, "/released/", path)


Compress(app)


if __name__ == "__main__":
    app.run(debug=True)

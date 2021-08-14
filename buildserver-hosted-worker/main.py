from flask import Flask

from common.rpc.buildserver_hosted_worker import build_worker_build
from common.rpc.secrets import only

DO_NOT_BUILD = "DO NOT BUILD"

app = Flask(__name__)
if __name__ == "__main__":
    app.debug = True


@build_worker_build.bind(app)
@only("buildserver", allow_staging=True)
def build_worker_build():
    ...


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True, threaded=False)

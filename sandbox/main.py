from flask import Flask, redirect

from common.oauth_client import create_oauth_client, is_staff
from common.url_for import url_for

app = Flask(__name__, static_folder="", static_url_path="")
if __name__ == "__main__":
    app.debug = True

create_oauth_client(app, "61a-staging")


@app.route("/")
def index():
    if not is_staff("cs61a"):
        return redirect(url_for("login"))
    return "<code>Welcome to the sandbox!</code>"


if __name__ == "__main__":
    app.run(debug=True)

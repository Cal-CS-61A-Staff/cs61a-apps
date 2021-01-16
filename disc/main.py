from flask import Flask, request

from common.db import connect_db, transaction_db
from common.oauth_client import (
    create_oauth_client,
    get_user,
    is_enrolled,
    login,
)

app = Flask(__name__, static_folder="", static_url_path="")
if __name__ == "__main__":
    app.debug = True


create_oauth_client(app, "61a-discussions")

with connect_db() as db:
    db(
        """CREATE TABLE IF NOT EXISTS saves (
    email varchar(128),
    key varchar(512),
    value LONGBLOB
);"""
    )


@app.route("index")
def index():
    return "<script> window.close(); </script>"


@app.route("/save", methods=["POST"])
def submit():
    if not is_enrolled("cs61a"):
        return login()
    email = get_user()["email"]
    key = request.json["key"]
    value = request.json["value"]

    with transaction_db() as db:
        db("DELETE FROM saves WHERE email=%s AND key=%s", [email, key])
        db(
            "INSERT INTO saves (email, key, value) VALUES (%s, %s, %s)",
            [email, key, value],
        )


if __name__ == "__main__":
    app.run(debug=True)

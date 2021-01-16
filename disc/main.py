from flask import Flask, jsonify, request
from flask_cors import cross_origin

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
    name varchar(512),
    value LONGBLOB
);"""
    )


@app.route("index")
def index():
    return "<script> window.close(); </script>"


@cross_origin(origin="cs61a.org")
@app.route("/save", methods=["POST"])
def save():
    if not is_enrolled("cs61a"):
        return login()
    email = get_user()["email"]
    name = request.json["name"]
    value = request.json["value"]

    with transaction_db() as db:
        db("DELETE FROM saves WHERE email=%s AND name=%s", [email, name])
        db(
            "INSERT INTO saves (email, name, value) VALUES (%s, %s, %s)",
            [email, name, value],
        )


@cross_origin(origin="cs61a.org")
@app.route("/fetch", methods=["POST"])
def fetch():
    if not is_enrolled("cs61a"):
        return login()
    email = get_user()["email"]
    with connect_db() as db:
        resp = db("SELECT name, value FROM saves WHERE email=%s", [email]).fetchall()
    return jsonify(dict(resp))


if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, Response, abort, jsonify, request, session
from flask.sessions import SecureCookieSessionInterface
from flask_cors import CORS, cross_origin

from common.db import connect_db, transaction_db
from common.oauth_client import (
    create_oauth_client,
    get_user,
    is_enrolled,
    login,
)

VALID_ORIGINS = r"https://.*cs61a\.org"

app = Flask(__name__, static_folder="", static_url_path="")
if __name__ == "__main__":
    app.debug = True

CORS(app, origins=VALID_ORIGINS, supports_credentials=True)

create_oauth_client(app, "61a-discussions")

"""
This is normally risky! It is safe here because 
    (a) CORS prevents an attacker from reading reply data, even if their request is authenticated
    (b) The endpoints require a Content-Type of application/json, so browsers will send a pre-flight
        meaning that they will not even send POSTs unless they pass the CORS check, which they don't

To ensure safety, we must ensure that 
    (a) GET requests have no side-effects
    (b) POST requests must have the JSON Content-Type, so a malicious site cannot send requests on
        behalf of a user that can cause issues.
    (c) The CORS policy only allows *.cs61a.org to send POSTs with credentials
"""


@app.after_request
def patch_session_samesite(response: Response):
    response.headers.add(
        "Set-Cookie",
        f"session={SecureCookieSessionInterface().get_signing_serializer(app).dumps(dict(session))}; "
        "HttpOnly; SameSite=Lax; Path=/; Secure;",
    )
    return response


with connect_db() as db:
    db(
        """CREATE TABLE IF NOT EXISTS saves (
    email varchar(128),
    name varchar(512),
    value LONGBLOB
);"""
    )


@app.route("/")
def index():
    return "<script> window.close(); </script>"


@app.route("/save", methods=["POST"])
def save():
    if not is_enrolled("cs61a"):
        abort(401)
    email = get_user()["email"]
    name = request.json["name"]
    value = request.json["value"]

    with transaction_db() as db:
        db("DELETE FROM saves WHERE email=%s AND name=%s", [email, name])
        db(
            "INSERT INTO saves (email, name, value) VALUES (%s, %s, %s)",
            [email, name, value],
        )

    return dict(success=True)


@app.route("/fetch", methods=["POST"])
def fetch():
    if not is_enrolled("cs61a"):
        abort(401)
    email = get_user()["email"]
    with connect_db() as db:
        resp = db("SELECT name, value FROM saves WHERE email=%s", [email]).fetchall()
    return jsonify(
        {
            name: value.decode("utf-8") if value is not None else None
            for name, value in resp
        }
    )


if __name__ == "__main__":
    app.run(debug=True)

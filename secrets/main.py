import hashlib
from functools import wraps
from typing import List, Tuple

from flask import Flask, abort, redirect, request, url_for

from common.course_config import is_admin, is_admin_token
from common.db import connect_db
from common.oauth_client import create_oauth_client, get_user, is_staff, login
from common.rpc.secrets import (
    create_master_secret,
    get_secret_from_server,
    load_all_secrets,
    validate_master_secret,
)
from common.secrets import new_secret

app = Flask(__name__, static_folder="", static_url_path="")
if __name__ == "__main__":
    app.debug = True

with connect_db() as db:
    db(
        """CREATE TABLE IF NOT EXISTS secrets (
    app varchar(128),
    name varchar(128),
    public_value varchar(512),
    staging_value varchar(512)
)"""
    )
    secret_key = db(
        "SELECT public_value FROM secrets WHERE app='secrets' and name='OKPY_OAUTH_SECRET'"
    ).fetchone()

create_oauth_client(app, "61a-secrets", secret_key[0] if secret_key is not None else "")


@validate_master_secret.bind(app)
def validate_master_secret(master_secret):
    with connect_db() as db:
        public_app = db(
            "SELECT app FROM secrets WHERE public_value=%s AND name='MASTER'",
            [master_secret],
        ).fetchone()
        if public_app is not None:
            return public_app[0], False
        staging_app = db(
            "SELECT app FROM secrets WHERE staging_value=%s AND name='MASTER'",
            [master_secret],
        ).fetchone()
        if staging_app is not None:
            return staging_app[0], True
        abort(401)


# intentional duplicate of the RPC decorator, since this calls
# the local version of validate_master_secret, not the RPC wrapper
def validates_master_secret(func):
    @wraps(func)
    def wrapped(
        *,
        master_secret=None,
        _sudo_token=None,
        _impersonate=None,
        _is_staging=False,
        **kwargs,
    ):
        if master_secret:
            app, is_staging = validate_master_secret(master_secret=master_secret)
            return func(app=app, is_staging=is_staging, **kwargs)
        elif _sudo_token and is_admin_token(_sudo_token, course="cs61a"):
            return func(app=_impersonate, is_staging=_is_staging, **kwargs)
        raise PermissionError

    return wrapped


@get_secret_from_server.bind(app)
@validates_master_secret
def get_secret(app, is_staging, secret_name):
    with connect_db() as db:
        public_value, staging_value = db(
            "SELECT public_value, staging_value FROM secrets WHERE app=%s AND name=%s",
            [app, secret_name],
        ).fetchone()
    if is_staging:
        return staging_value
    else:
        return public_value


@load_all_secrets.bind(app)
@validates_master_secret
def load_all_secrets(app, is_staging, created_app_name):
    if app != "buildserver" or is_staging:
        abort(403)  # only buildserver running in prod can view all secrets
    with connect_db() as db:
        return dict(
            db(
                "SELECT name, public_value FROM secrets WHERE app=%s",
                [created_app_name],
            ).fetchall()
        )


@create_master_secret.bind(app)
@validates_master_secret
def create_master_secret(app, is_staging, created_app_name):
    if app != "buildserver" or is_staging:
        abort(403)  # only buildserver running in prod can create new apps
    with connect_db() as db:
        out = db(
            "SELECT public_value, staging_value FROM secrets WHERE app=%s AND name='MASTER'",
            [created_app_name],
        ).fetchone()
        if out is not None:
            return list(out)
        out = new_secret(), new_secret()
        db(
            "INSERT INTO secrets (app, name, public_value, staging_value) VALUES (%s, %s, %s, %s)",
            [created_app_name, "MASTER", *out],
        )
    return out


def display_hash(secret: str):
    return hashlib.md5(secret.encode("utf-8")).hexdigest()[:8]


@app.route("/")
def index():
    if not is_staff("cs61a"):
        return login()
    with connect_db() as db:
        secrets: List[Tuple[str, str, str, str]] = db(
            "SELECT app, name, public_value, staging_value FROM secrets"
        ).fetchall()
    return """
    <h1>Secrets Tool</h1>
    <p>
        Add a secret: 
        <form action="/create_secret" method="POST">
            <input name="app" placeholder="App name" /> 
            <input name="name" placeholder="Secret name" /> 
            <input name="public" placeholder="Public value" /> 
            <input name="staging" placeholder="Staging value" />
            <button type="submit">Submit</button>
        </form>
    </p>
    <p>
        You should assume that the staging value is visible to any member of 61A staff.
        For instance, for Auth keys, provide a 61A-specific key for the staging value,
        and a super key only for the public value, to avoid leaking information. That said,
        staging values are not directly exposed and access will be logged in deploy logs,
        so don't worry about it too much, just be careful.
    </p>
    """ + "".join(
        f"""<p>
            <form 
                style="display: inline" 
                action="{url_for("delete_secret", app_name=app, secret_name=name)}" 
                method="post"
            >
                {app}/{name} - {display_hash(public_value)} (staging: {display_hash(staging_value)})
                <input type="submit" value="Remove">
        </form>"""
        for app, name, public_value, staging_value in secrets
    )


@app.route("/create_secret", methods=["POST"])
def create_secret():
    if not is_staff("cs61a"):
        return login()
    app = request.form["app"]
    name = request.form["name"]
    public = request.form["public"]
    staging = request.form["staging"]
    with connect_db() as db:
        existing = db(
            "SELECT * FROM secrets WHERE app=%s AND name=%s", [app, name]
        ).fetchall()
        if existing:
            abort(409)
        db(
            "INSERT INTO secrets (app, name, public_value, staging_value) VALUES (%s, %s, %s, %s)",
            [app, name, public, staging],
        )
    return redirect(url_for("index"))


@app.route("/delete_secret/<app_name>/<secret_name>", methods=["POST"])
def delete_secret(app_name, secret_name):
    if not is_admin(get_user()["email"], "cs61a"):
        return login()
    with connect_db() as db:
        db("DELETE FROM secrets WHERE app=%s AND name=%s", [app_name, secret_name])
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)

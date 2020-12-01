import os
from base64 import b64decode
from contextlib import contextmanager
from functools import wraps
from os.path import abspath
from pathlib import Path
from random import randrange
from subprocess import CalledProcessError
from typing import Optional

import requests
from flask import Flask, g, jsonify, redirect, safe_join, send_file

from common.course_config import get_endpoint
from common.db import connect_db
from common.oauth_client import (
    AUTHORIZED_ROLES,
    create_oauth_client,
    is_staff,
)
from common.rpc.hosted import add_domain
from common.rpc.sandbox import (
    get_server_hashes,
    initialize_sandbox,
    is_sandbox_initialized,
    run_incremental_build,
    update_file,
)
from common.rpc.secrets import get_secret
from common.shell_utils import sh
from common.url_for import get_host, url_for
from sicp.build import get_hash, hash_all

app = Flask(__name__)
if __name__ == "__main__":
    app.debug = True

WORKING_DIRECTORY = abspath("tmp") if app.debug else "/save"
HOT_RELOAD_SCRIPT_PATH = abspath("hot_reloader.js")
REPO = "Cal-CS-61A-Staff/berkeley-cs61a"

DEFAULT_USER = "rahularya"

create_oauth_client(app, "61a-sandbox")

with connect_db() as db:
    db(
        """CREATE TABLE IF NOT EXISTS sandboxes (
    username varchar(128),
    initialized boolean,
    locked boolean,
    version integer
)"""
    )


def is_staff_userdata(userdata):
    endpoint = get_endpoint(course="cs61a")
    for participation in userdata["participations"]:
        if participation["role"] not in AUTHORIZED_ROLES:
            continue
        if participation["course"]["offering"] != endpoint:
            continue
        return True
    return False


def verifies_access_token(func):
    @wraps(func)
    def decorated(**kwargs):
        token = kwargs.pop("access_token")
        ret = requests.get(
            "https://okpy.org/api/v3/user/", params={"access_token": token}
        )
        if ret.status_code != 200:
            raise PermissionError
        g.email = ret.json()["data"]["email"]
        if not is_staff_userdata(ret.json()["data"]) or not g.email.endswith(
            "@berkeley.edu"
        ):
            raise PermissionError
        g.username = g.email[: -len("@berkeley.edu")]
        return func(**kwargs)

    return decorated


def is_prod_build():
    return not app.debug and ".pr." not in get_host() and "cs61a" in get_host()


@contextmanager
def sandbox_lock():
    try:
        with connect_db() as db:
            locked = db(
                "SELECT locked FROM sandboxes WHERE username=%s", [g.username]
            ).fetchone()
            if locked is None:
                # sandbox does not exist
                db(
                    "INSERT INTO sandboxes (username, initialized, locked) VALUES (%s, FALSE, TRUE)",
                    [g.username],
                )
                yield
            else:
                [locked] = locked
                if locked:
                    # TODO: Some way to force an unlock from the CLI
                    raise BlockingIOError(
                        "Another operation is currently taking place in the sandbox"
                    )
                else:
                    db(
                        "UPDATE sandboxes SET locked=TRUE WHERE username=%s",
                        [g.username],
                    )
                    yield

    finally:
        with connect_db() as db:
            db("UPDATE sandboxes SET locked=FALSE WHERE username=%s", [g.username])


def get_working_directory():
    if is_prod_build():
        return os.path.join(WORKING_DIRECTORY, g.username)
    else:
        # Everyone shares the same working directory on dev / PR builds
        return WORKING_DIRECTORY


@app.route("/")
@app.route("/<path:path>", strict_slashes=False)
def index(path="index.html"):
    if not is_staff("cs61a"):
        return redirect(url_for("login"))
    target = get_working_directory() + "/published/" + path
    if os.path.isdir(target):
        return index(path + "/index.html")
    path = safe_join(get_working_directory(), "published", path)
    if path.endswith(".html"):
        with open(path, "r") as f:
            out = f.read()
        out += """<script src="/hot_reloader.js"> </script>"""
        return out
    else:
        return send_file(path)


def get_status():
    with connect_db() as db:
        version = db(
            "SELECT version, locked FROM sandboxes WHERE username=%s",
            get_host().split(".")[0] if is_prod_build() else DEFAULT_USER,
        ).fetchone()
        if version is None:
            return 0, False
        else:
            return list(version)


@app.route("/hot_reloader.js")
def hot_reloader():
    if not is_staff("cs61a"):
        return redirect(url_for("login"))

    with open(HOT_RELOAD_SCRIPT_PATH) as f:
        out = f.read().replace("VERSION", str(get_status()[0]))
    return out


@app.route("/latest_revision", methods=["POST"])
def latest_revision():
    version, building = get_status()
    return jsonify(dict(version=version, isLoading=building))


@update_file.bind(app)
@verifies_access_token
def update_file(
    path: str,
    encoded_file_contents: Optional[str] = None,
    symlink: Optional[str] = None,
    delete: bool = False,
):
    base = get_working_directory()
    target = safe_join(base, path)
    del path
    if delete:
        if os.path.islink(target):
            os.unlink(target)
        elif os.path.exists(target):
            os.remove(target)
    else:
        target = Path(target)
        target.parent.mkdir(parents=True, exist_ok=True)

        if symlink:
            if os.path.islink(target):
                os.unlink(target)
            elif os.path.exists(target):
                os.remove(target)

            os.symlink(symlink, target)
        else:
            decoded_file_contents = b64decode(encoded_file_contents.encode("ascii"))
            with open(target, "wb+") as f:
                f.write(decoded_file_contents)

        assert get_hash(target) is not None


@run_incremental_build.bind(app)
@verifies_access_token
def run_incremental_build(clean=False):
    with sandbox_lock():
        os.chdir(get_working_directory())
        os.chdir("src")
        try:
            if clean:
                sh("make", "VIRTUAL_ENV=../env", "clean")
            sh("make", "VIRTUAL_ENV=../env", "all", "unreleased", capture_output=True)
        except CalledProcessError as e:
            raise Exception(e.stdout.decode("utf-8") + "\n" + e.stderr.decode("utf-8"))
    with connect_db() as db:
        db(
            "UPDATE sandboxes SET version=%s WHERE username=%s",
            [randrange(1000), g.username],
        )


@get_server_hashes.bind(app)
@verifies_access_token
def get_server_hashes():
    base = get_working_directory()
    os.chdir(base)
    return hash_all()


@is_sandbox_initialized.bind(app)
@verifies_access_token
def is_sandbox_initialized():
    with connect_db() as db:
        if not db(
            "SELECT initialized FROM sandboxes WHERE username=%s", [g.username]
        ).fetchone()[0]:
            return False
        if is_prod_build():
            # sanity check that the working directory exists
            return os.path.exists(get_working_directory())
        else:
            # temp directory always exists
            return True


@initialize_sandbox.bind(app)
@verifies_access_token
def initialize_sandbox(force=False):
    with sandbox_lock():
        initialized = is_sandbox_initialized()
        if initialized and not force:
            raise Exception("Sandbox is already initialized")
        elif initialized:
            sh("rm", "-rf", get_working_directory())
        Path(get_working_directory()).mkdir(parents=True, exist_ok=True)
        os.chdir(get_working_directory())
        sh("git", "init")
        sh(
            "git",
            "fetch",
            "--depth=1",
            f"https://{get_secret(secret_name='GITHUB_ACCESS_TOKEN')}@github.com/{REPO}",
            "master",
        )
        sh("git", "checkout", "FETCH_HEAD", "-f")
        if is_prod_build():
            add_domain(name="sandbox", domain=f"{g.username}.sb.cs61a.org")
        with connect_db() as db:
            db("UPDATE sandboxes SET initialized=TRUE WHERE username=%s", [g.username])


if __name__ == "__main__":
    app.run()

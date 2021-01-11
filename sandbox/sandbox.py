import os
import threading
from base64 import b64decode
from contextlib import contextmanager
from functools import wraps
from os.path import abspath
from pathlib import Path
from random import randrange
from subprocess import CalledProcessError
from typing import Optional

import requests
from flask import Flask, abort, g, jsonify, request, safe_join, send_file

from common.course_config import get_endpoint
from common.db import connect_db
from common.oauth_client import (
    AUTHORIZED_ROLES,
    create_oauth_client,
    is_staff,
    login,
)
from common.rpc.hosted import add_domain
from common.rpc.paste import get_paste, get_paste_url, paste_text
from common.rpc.sandbox import (
    get_server_hashes,
    initialize_sandbox,
    is_sandbox_initialized,
    run_make_command,
    update_file,
)
from common.rpc.secrets import get_secret
from common.shell_utils import sh
from common.url_for import get_host, url_for
from sicp.build import get_hash, hash_all

from utils import db_lock

app = Flask(__name__)
if __name__ == "__main__":
    app.debug = True

WORKING_DIRECTORY = abspath("tmp") if app.debug else "/save"
HOT_RELOAD_SCRIPT_PATH = abspath("hot_reloader.js")
PDFJS_DIRECTORY = abspath("pdfjs")
REPO = "Cal-CS-61A-Staff/berkeley-cs61a"

ENV = dict(
    CLOUD_STORAGE_BUCKET="website-pdf-cache.buckets.cs61a.org", IN_SANDBOX="true"
)

DEFAULT_USER = "prbuild"

PDF_INLINE_SCRIPT = """
<div style="width: 100%; height: 100%;">
    <iframe 
        src="/pdfjs/web/viewer.html?file=SRC_PATH" 
        style="width: 100%; height: 100%;" 
        frameborder="0" 
        scrolling="no"
    >
    </iframe>
</div>
"""

HOT_RELOAD_INLINE_SCRIPT = """
<script>
    const version=VERSION; 
    const manualVersion=MANUAL_VERSION;
</script>
<script src="/hot_reloader.js"></script>
"""

create_oauth_client(app, "61a-sandbox")

with connect_db() as db:
    db(
        """CREATE TABLE IF NOT EXISTS sandboxes (
    username varchar(128),
    initialized boolean,
    locked boolean,
    version integer, -- updated every time we sync a file
    manual_version integer -- updated after every manual make command
);"""
    )

    db(
        """CREATE TABLE IF NOT EXISTS builds (
        username varchar(128),
        target varchar(256),
        pending boolean
    );"""
    )

    db(
        """CREATE TABLE IF NOT EXISTS targets (
        username varchar(128),
        target varchar(256),
        logs varchar(128),
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
        g.username = (
            g.email[: -len("@berkeley.edu")] if is_prod_build() else DEFAULT_USER
        )
        return func(**kwargs)

    return decorated


def is_prod_build():
    return not app.debug and ".pr." not in get_host() and "cs61a" in get_host()


def get_working_directory(username):
    return os.path.join(WORKING_DIRECTORY, username, "berkeley-cs61a")


def get_host_username():
    return get_host().split(".")[0] if is_prod_build() else DEFAULT_USER


def path_to_target(path):
    return safe_join("../published", path)


@app.route("/")
@app.route("/<path:path>", strict_slashes=False)
def index(path="index.html"):
    if not is_staff("cs61a"):
        return login()
    username = get_host_username()
    base_directory = get_working_directory(username)

    if "." not in path:
        return index(path + "/index.html")

    original_path = path
    target = path_to_target(path)
    path = safe_join(base_directory, "published", path)
    if not is_up_to_date(username, target):
        build(username, target)

    if path.endswith(".html") or path.endswith(".pdf"):
        logs = get_logs(username, target)
        if logs is not None:
            name, data = logs
            out = f"""
                <pre>{data}</pre>
                <a href={get_paste_url(name)}>{get_paste_url(name)}</a>
                """
        elif os.path.exists(path):
            if path.endswith(".pdf"):
                out = PDF_INLINE_SCRIPT.replace("SRC_PATH", "/raw/" + original_path)
            else:
                with open(path, "r") as f:
                    out = f.read()
        else:
            out = ""
        out += HOT_RELOAD_INLINE_SCRIPT.replace(
            "MANUAL_VERSION", str(get_manual_version(username))
        ).replace(
            "VERSION",
            str(get_version(username, target)),
        )
        return out
    else:
        try:
            return send_file(path, cache_timeout=-1)
        except FileNotFoundError:
            return "", 404


@app.route("/raw/<path:path>")
def raw(path):
    if not is_staff("cs61a"):
        abort(403)

    path = safe_join(get_working_directory(get_host_username()), "published", path)
    try:
        return send_file(path, cache_timeout=-1)
    except FileNotFoundError:
        return "", 404


@app.route("/pdfjs/<path:path>")
def pdfjs(path):
    path = safe_join(PDFJS_DIRECTORY, path)
    try:
        return send_file(path)
    except FileNotFoundError:
        return "", 404


def get_src_version(username):
    with connect_db() as db:
        version = db(
            "SELECT version FROM sandboxes WHERE username=%s",
            [username],
        ).fetchone()
        if version is None:
            return 0
        else:
            return version[0] or 0


def get_manual_version(username):
    with connect_db() as db:
        manual_version = db(
            "SELECT manual_version FROM sandboxes WHERE username=%s",
            [username],
        ).fetchone()
        if manual_version is None:
            return 0
        else:
            return manual_version[0] or 0


@app.route("/hot_reloader.js")
def hot_reloader():
    if not is_staff("cs61a"):
        abort(403)

    return send_file(HOT_RELOAD_SCRIPT_PATH)


@app.route("/get_revision", methods=["POST"])
def get_revision():
    if not is_staff("cs61a"):
        abort(403)
    path = request.json["path"]
    src_version = get_src_version(get_host_username())
    manual_version = get_manual_version(get_host_username())
    version = get_version(get_host_username(), path_to_target(path))
    return jsonify(
        dict(pubVersion=version, srcVersion=src_version, manualVersion=manual_version)
    )


@app.route("/rebuild_path", methods=["POST"])
def rebuild_path():
    if not is_staff("cs61a"):
        abort(403)
    path = request.json["path"]
    build(get_host_username(), path_to_target(path))
    return ""


@update_file.bind(app)
@verifies_access_token
def update_file(
    path: str,
    encoded_file_contents: Optional[str] = None,
    symlink: Optional[str] = None,
    delete: bool = False,
):
    base = get_working_directory(g.username)
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

    with connect_db() as db:
        db(
            "UPDATE sandboxes SET version=%s WHERE username=%s",
            [randrange(1, 1000), g.username],
        )


@run_make_command.bind(app)
@verifies_access_token
def run_make_command(target):
    os.chdir(get_working_directory(g.username))
    os.chdir("src")

    clear_pending_builds(g.username)

    try:
        yield from sh(
            "make",
            "VIRTUAL_ENV=../env",
            target,
            env=ENV,
            stream_output=True,
            shell=True,
        )

    finally:
        increment_manual_version(g.username)


def increment_manual_version(username):
    with connect_db() as db:
        db(
            "UPDATE sandboxes SET manual_version=%s, version=%s WHERE username=%s",
            [randrange(1, 1000), randrange(1, 1000), username],
        )


def get_pending_targets(username):
    with connect_db() as db:
        return [
            target
            for [target] in db(
                "SELECT target FROM builds WHERE username=%s AND pending=TRUE",
                [username],
            ).fetchall()
        ]


def clear_pending_builds(username):
    with connect_db() as db:
        db(
            "UPDATE builds SET pending=FALSE WHERE username=%s",
            [username],
        )


def build(username, target):
    pending = get_pending_targets(username)
    if target in pending:
        # target is already scheduled to be built
        return
    with connect_db() as db:
        db(
            "INSERT INTO builds (username, target, pending) VALUES (%s, %s, %s)",
            [username, target, True],
        )
    if not pending:
        # We need to start the build ourselves
        with app.app_context():
            threading.Thread(target=build_worker, args=[username]).start()


def get_version(username, target):
    with connect_db() as db:
        version = db(
            "SELECT version FROM targets WHERE username=%s AND target=%s",
            [username, target],
        ).fetchone()
        if version is None:
            return 0
        else:
            return version[0]


def update_version(username, target, version, logs=None):
    old_version = get_version(username, target)
    with connect_db() as db:
        if old_version:
            db(
                "UPDATE targets SET version=%s, logs=%s WHERE username=%s AND target=%s",
                [version, logs, username, target],
            )
        else:
            db(
                "INSERT INTO targets (username, target, version, logs) VALUES (%s, %s, %s, %s)",
                [username, target, version, logs],
            )


def is_up_to_date(username, target):
    src_version = get_src_version(username)
    curr_version = get_version(username, target)
    return src_version == curr_version


def get_logs(username, target):
    with connect_db() as db:
        logs = db(
            "SELECT logs FROM targets WHERE username=%s AND target=%s",
            [username, target],
        ).fetchone()
        if logs is not None and logs[0] is not None:
            return logs[0], get_paste(name=logs[0])
        else:
            return None


def build_worker(username):
    # Note that we are not necessarily running in an app context
    try:
        while True:
            targets = get_pending_targets(username)
            if not targets:
                break
            target = targets[0]
            src_version = get_src_version(username)
            os.chdir(get_working_directory(username))
            os.chdir("src")
            ok = False
            try:
                sh("make", "-n", "VIRTUAL_ENV=../env", target, env=ENV)
            except CalledProcessError as e:
                if e.returncode == 2:
                    # target does not exist, no need to build
                    update_version(username, target, src_version)
                    ok = True
            if not ok:
                # target exists, time to build!
                try:
                    sh(
                        "make",
                        "VIRTUAL_ENV=../env",
                        target,
                        env={**ENV, "LAZY_LOADING": "true"},
                        capture_output=True,
                        quiet=True,
                    )
                except CalledProcessError as e:
                    log_name = paste_text(
                        data=(
                            (e.stdout or b"").decode("utf-8")
                            + (e.stderr or b"").decode("utf-8")
                        )
                    )
                    update_version(username, target, src_version, log_name)
                else:
                    update_version(username, target, src_version)
            with connect_db() as db:
                db(
                    "UPDATE builds SET pending=FALSE WHERE username=%s AND target=%s",
                    [username, target],
                )
    except:
        # in the event of failure, cancel all builds and trigger refresh
        increment_manual_version(username)
        clear_pending_builds(username)
        raise


@get_server_hashes.bind(app)
@verifies_access_token
def get_server_hashes():
    base = get_working_directory(g.username)
    os.chdir(base)
    return hash_all()


@is_sandbox_initialized.bind(app)
@verifies_access_token
def is_sandbox_initialized():
    return check_sandbox_initialized(g.username)


def check_sandbox_initialized(username):
    with connect_db() as db:
        initialized = db(
            "SELECT initialized FROM sandboxes WHERE username=%s", [username]
        ).fetchone()
    if initialized is None or not initialized[0]:
        return False
    # sanity check that the working directory exists
    return os.path.exists(get_working_directory(username))


@initialize_sandbox.bind(app)
@verifies_access_token
def initialize_sandbox(force=False):
    with db_lock("sandboxes", g.username):
        initialized = check_sandbox_initialized(g.username)
        if initialized and not force:
            raise Exception("Sandbox is already initialized")
        elif initialized:
            sh("rm", "-rf", get_working_directory(g.username))
        Path(get_working_directory(g.username)).mkdir(parents=True, exist_ok=True)
        os.chdir(get_working_directory(g.username))
        sh("git", "init")
        sh(
            "git",
            "fetch",
            "--depth=1",
            f"https://{get_secret(secret_name='GITHUB_ACCESS_TOKEN')}@github.com/{REPO}",
            "master",
        )
        sh("git", "checkout", "FETCH_HEAD", "-f")
        os.mkdir("published")  # needed for lazy-loading builds
        if is_prod_build():
            add_domain(name="sandbox", domain=f"{g.username}.sb.cs61a.org")
        with connect_db() as db:
            db("UPDATE sandboxes SET initialized=TRUE WHERE username=%s", [g.username])


if __name__ == "__main__":
    app.run()

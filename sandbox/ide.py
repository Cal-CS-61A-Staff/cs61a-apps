import os, shutil, subprocess, sys, yaml, socket
from contextlib import contextmanager
from flask import Flask, request, url_for, redirect
from werkzeug.security import gen_salt
from functools import wraps
from utils import db_lock, Server, Location

from common.oauth_client import (
    create_oauth_client,
    is_staff,
    login,
    get_user,
)
from common.rpc.hosted import add_domain
from common.rpc.secrets import get_secret
from common.shell_utils import sh
from common.html import html
from common.url_for import get_host
from common.db import connect_db

HOSTNAME = os.environ.get("HOSTNAME", "cs61a.org")
NGINX_PORT = os.environ.get("PORT", "8001")

DEFAULT_USER = "prbuild"

app = Flask(__name__)

create_oauth_client(
    app, "61a-ide", secret_key=get_secret(secret_name="OKPY_IDE_SECRET")
)

with connect_db() as db:
    db(
        """CREATE TABLE IF NOT EXISTS ide (
    username varchar(128),
    initialized boolean, -- this is unused in the ide context
    locked boolean
);"""
    )


@app.route("/")
@auth_only
def index():
    username = get_username()

    out = "<h1>61A Sandbox IDE</h1>\n"
    out += f"Hi {get_user()['name'].split()[0]}! Your IDE is "

    if not get_server_pid(username):
        out += "inactive.<br />"
        out += f"""<form action="{url_for('start')}" method="POST">
        <input type="hidden" name="username" value="{username}" />
        <input type="submit" value="Start IDE" />
        </form>"""
        return html(out)

    config = get_config(username)

    out += "active.<br />"
    out += f"""<form action="https://{username}.{get_host()}/login", method="POST" target="_blank">
    <input type="hidden" name="base" value="" /><input type="hidden" name="password" value="{config['password']}" />
    <input type="submit" value="Open in New Tab" />
    </form><form action="{url_for('kill')}" method="POST">
    <input type="hidden" name="username" value="{username}" />
    <input type="submit" value="Kill IDE" />
    </form>"""

    return html(out)


@app.route("/start", methods=["POST"])
@auth_only
def start():
    username = request.form.get("username")

    try:
        sh("id", "-u", username)
        user_exists = True
    except subprocess.CalledProcessError:
        user_exists = False

    if not user_exists:
        sh("useradd", "-b", "/save", "-m", username, "-s", "/bin/bash")
        if HOSTNAME == "cs61a.org":
            add_domain(
                name=get_hosted_app_name(),
                domain=f"{username}.{get_host()}",
                proxy_set_header={
                    "Host": "$host",
                    "Upgrade": "$http_upgrade",
                    "Connection": "upgrade",
                    "Accept-Encoding": "gzip",
                },
            )

    if not get_server_pid(username):
        with db_lock("ide", username):
            passwd = gen_salt(24)

            config = {
                "socket": f"/tmp/ide-{username}.sock",
                "auth": "password",
                "password": passwd,
                "home": f"https://{get_host()}",
            }

            with open(f"/save/{username}/.code-server.yaml", "w") as csc:
                yaml.dump(config, csc)

            subprocess.Popen(get_server_cmd(username))
            sh("sleep", "2")  # give the server a couple of seconds to start up
            sh("chmod", "666", f"/tmp/ide-{username}.sock")

            conf = Server(
                Location(
                    "/",
                    include="proxy_params",
                    proxy_pass=f"http://unix:/tmp/ide-{username}.sock",
                    proxy_set_header={
                        "Host": "$host",
                        "Upgrade": "$http_upgrade",
                        "Connection": "upgrade",
                        "Accept-Encoding": "gzip",
                    },
                ),
                server_name=f"{username}.{get_host()}",
                listen=NGINX_PORT,
                error_page=f"502 https://{get_host()}",
            )

            with open(f"/etc/nginx/sites-enabled/{username}.{get_host()}", "w") as f:
                f.write(str(conf))
            sh("nginx", "-s", "reload")

    if not os.path.exists(f"/save/{username}/berkeley-cs61a"):
        if os.path.exists("/save/berkeley-cs61a"):
            shutil.copytree(
                "/save/berkeley-cs61a",
                f"/save/{username}/berkeley-cs61a",
                symlinks=True,
            )
            sh("chown", "-R", username, f"/save/{username}/berkeley-cs61a")

    return redirect(url_for("index"))


@app.route("/kill", methods=["POST"])
@auth_only
def kill():
    username = request.form.get("username")
    pid = get_server_pid(username)

    if pid:
        sh("kill", pid.decode("utf-8")[:-1])
        sh("sleep", "2")  # give the server a couple of seconds to shutdown
    return redirect(url_for("index"))


def auth_only(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        if not is_staff("cs61a") or not is_berkeley():
            return login()
        return func(*args, **kwargs)

    return wrapped


def is_prod_build():
    return ".pr." not in get_host() and "cs61a" in get_host()


def get_hosted_app_name():
    return "sandbox" if is_prod_build() else f"sandbox-pr{get_host().split['.'][0]}"


def get_username():
    return get_user()["email"].split("@")[0] if is_prod_build() else DEFAULT_USER


def is_berkeley():
    return get_user()["email"].endswith("@berkeley.edu")


def get_server_cmd(username):
    return [
        "su",
        username,
        "-c",
        f"code-server --config /save/{username}/.code-server.yaml",
    ]


def get_server_pid(username):
    try:
        return sh(
            "pgrep", "-f", " ".join(get_server_cmd(username)), capture_output=True
        )
    except subprocess.CalledProcessError:
        return False


def get_config(username):
    with open(f"/save/{username}/.code-server.yaml") as csc:
        data = yaml.load(csc)
    return data


if __name__ == "__main__":
    app.run()

import os, shutil, subprocess, sys, yaml, socket
from contextlib import contextmanager
from flask import Flask, request, redirect
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
from common.url_for import get_host, url_for
from common.db import connect_db

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
    initialized boolean, -- this is unused in the ide context, for now
    locked boolean
);"""
    )


def auth_only(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        if not is_staff("cs61a") or not is_berkeley():
            return login()
        return func(*args, **kwargs)

    return wrapped


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
        print(f"User {username} doesn't exist, creating...", file=sys.stderr)
        sh("useradd", "-b", "/save", "-m", username, "-s", "/bin/bash")
        print(
            f"Proxying {username}.{get_host()} to {get_hosted_app_name()}...",
            file=sys.stderr,
        )
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
        print(f"Server for {username} is not running, starting...", file=sys.stderr)
        with db_lock("ide", username):
            passwd = gen_salt(24)
            port = get_open_port()

            config = {
                "port": port,
                "auth": "password",
                "password": passwd,
                "home": f"https://{get_host()}",
            }

            with open(f"/save/{username}/.code-server.yaml", "w") as csc:
                yaml.dump(config, csc)

            print("Configuration ready.", file=sys.stderr)

            sanitized = os.environ.copy()
            del sanitized["DATABASE_URL"]
            del sanitized["APP_HOME"]
            del sanitized["APP_MASTER_SECRET"]
            del sanitized["ENV"]
            del sanitized["INSTANCE_CONNECTION_NAME"]

            print("Environment sanitized.", file=sys.stderr)

            subprocess.Popen(get_server_cmd(username), env=sanitized)
            print("Subprocess opened.", file=sys.stderr)

            conf = Server(
                Location(
                    "/",
                    include="proxy_params",
                    proxy_pass=f"http://127.0.0.1:{port}",
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
            print("NGINX configuration written and server restarted.", file=sys.stderr)

    if not os.path.exists(f"/save/{username}/berkeley-cs61a"):
        print(f"Copy of repo for {username} not found, copying...", file=sys.stderr)
        if os.path.exists("/save/berkeley-cs61a"):
            print("Found a known good repo to copy.", file=sys.stderr)
            shutil.copytree(
                "/save/berkeley-cs61a",
                f"/save/{username}/berkeley-cs61a",
                symlinks=True,
            )
            sh("chown", "-R", username, f"/save/{username}/berkeley-cs61a")
            print("Tree copied and tree owner changed.", file=sys.stderr)

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


def is_prod_build():
    return ".pr." not in get_host() and "cs61a" in get_host()


def get_hosted_app_name():
    return "sandbox" if is_prod_build() else f"sandbox-pr{get_host().split('.')[0]}"


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


def get_open_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))

    s.listen(1)
    port = s.getsockname()[1]

    s.close()
    return port


if __name__ == "__main__":
    app.run()

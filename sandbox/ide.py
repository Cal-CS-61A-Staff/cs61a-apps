import os, shutil, subprocess, sys, yaml, socket, requests, time
from contextlib import contextmanager
from flask import Flask, request, redirect, session
from werkzeug.security import gen_salt
from functools import wraps
from utils import (
    db_lock,
    Server,
    Location,
    get_server_cmd,
    get_server_pid,
    get_active_servers,
    is_software_ta,
)

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
SK_RETURN_TO = "start_kill_return_to"

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


VSCODE_ASSOC = """
{
    "files.associations": {
        "BUILD": "python",
        "WORKSPACE": "python"
    },
    "files.trimTrailingWhitespace": true
}
"""


def auth_only(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        if not is_staff("cs61a") or not is_berkeley():
            return login()
        return func(*args, **kwargs)

    return wrapped


def gen_index_html(out, username, show_active=False):
    if not get_server_pid(username):
        out += "inactive or nonexistent.<br />"
        out += f"""<form action="{url_for('start')}" method="POST">
        <input type="hidden" name="username" value="{username}" />
        <input type="submit" value="Start IDE" />
        </form>"""
        return html(out)

    config = get_config(username)

    if is_prod_build():
        domain = f"{username}.{get_host()}"
    else:
        domain = f"{username}-{get_host()}"

    out += "active.<br />"
    out += f"""<form action="https://{domain}/login", method="POST">
    <input type="hidden" name="base" value="" /><input type="hidden" name="password" value="{config['password']}" />
    <input type="submit" value="Open IDE" />
    </form><form action="{url_for('kill')}" method="POST">
    <input type="hidden" name="username" value="{username}" />
    <input type="submit" value="Kill IDE" />
    </form>"""

    active = get_active_servers()
    if active and show_active:
        out += "<p>Active servers: " + ", ".join(active) + "</p>"

    return html(out)


@app.route("/")
@auth_only
def index():
    username = get_username()

    out = "<h1>61A Sandbox IDE</h1>\n"
    out += f"Hi {get_user()['name'].split()[0]}! Your IDE is "

    session[SK_RETURN_TO] = url_for("index")
    return gen_index_html(out, username, is_software_ta(get_user()["email"]))


@app.route("/sudo/<username>")
@auth_only
def sudo(username):
    if not is_software_ta(get_user()["email"]):
        return redirect(url_for("index"))

    out = "<h1>61A Sandbox IDE</h1>\n"
    out += f"Hi {get_user()['name'].split()[0]}! {username}'s IDE is "

    session[SK_RETURN_TO] = url_for("sudo", username=username)
    return gen_index_html(out, username, True)


@app.route("/start", methods=["POST"])
@auth_only
def start():
    username = request.form.get("username")

    try:
        sh("id", "-u", username)
        user_exists = True
    except subprocess.CalledProcessError:
        user_exists = False

    if is_prod_build():
        domain = f"{username}.{get_host()}"
    else:
        domain = f"{username}-{get_host()}"

    if not user_exists:
        print(f"User {username} doesn't exist, creating...", file=sys.stderr)
        sh("useradd", "-b", "/save", "-m", username, "-s", "/bin/bash")
        print(
            f"Proxying {domain} to {get_hosted_app_name()}...",
            file=sys.stderr,
        )
        add_domain(
            name=get_hosted_app_name(),
            domain=domain,
            proxy_set_header={
                "Host": "$host",
                "Upgrade": "$http_upgrade",
                "Connection": "upgrade",
                "Accept-Encoding": "gzip",
            },
        )

    sh("chown", "-R", username, f"/save/{username}")
    print("Home folder owner set.", file=sys.stderr)

    if not get_server_pid(username):
        print(f"Server for {username} is not running, starting...", file=sys.stderr)
        with db_lock("ide", username):
            passwd = gen_salt(24)
            port = get_open_port()

            config = {
                "bind-addr": f"127.0.0.1:{port}",
                "auth": "password",
                "password": passwd,
            }

            with open(f"/save/{username}/.code-server.yaml", "w") as csc:
                yaml.dump(config, csc)

            sh("chown", "-R", username, f"/save/{username}/.code-server.yaml")
            print("Configuration ready.", file=sys.stderr)

            sanitized = os.environ.copy()
            del sanitized["DATABASE_URL"]
            del sanitized["APP_HOME"]
            del sanitized["APP_MASTER_SECRET"]
            del sanitized["ENV"]
            del sanitized["INSTANCE_CONNECTION_NAME"]
            sanitized["PORT"] = str(port)

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
                server_name=domain,
                listen=NGINX_PORT,
                error_page=f"502 https://{get_host()}",
            )

            with open(f"/etc/nginx/sites-enabled/{domain}", "w") as f:
                f.write(str(conf))
            sh("nginx", "-s", "reload")
            print("NGINX configuration written and server restarted.", file=sys.stderr)

    if not os.path.exists(f"/save/{username}/berkeley-cs61a"):
        print(f"Copy of repo for {username} not found.", file=sys.stderr)
        if os.path.exists("/save/root/berkeley-cs61a"):
            print("Found a known good repo, copying...", file=sys.stderr)
            shutil.copytree(
                "/save/root/berkeley-cs61a",
                f"/save/{username}/berkeley-cs61a",
                symlinks=True,
            )
            print(
                "Tree copied. Writing Visual Studio Code associations...",
                file=sys.stderr,
            )
            os.mkdir(f"/save/{username}/berkeley-cs61a/.vscode")
            with open(
                f"/save/{username}/berkeley-cs61a/.vscode/settings.json", "w"
            ) as f:
                f.write(VSCODE_ASSOC)
            print("Done.", file=sys.stderr)
            sh("chown", "-R", username, f"/save/{username}/berkeley-cs61a")
            print("Tree owner changed.", file=sys.stderr)

    print("Waiting for code-server to come alive, if needed...", file=sys.stderr)
    while requests.get(f"https://{domain}").status_code != 200:
        time.sleep(1)
    print("code-server is alive.", file=sys.stderr)

    print("IDE ready.", file=sys.stderr)
    return redirect(session.pop(SK_RETURN_TO, url_for("index")))


@app.route("/kill", methods=["POST"])
@auth_only
def kill():
    username = request.form.get("username")
    pid = get_server_pid(username)

    if pid:
        sh("kill", pid.decode("utf-8")[:-1])
        sh("sleep", "2")  # give the server a couple of seconds to shutdown
    return redirect(session.pop(SK_RETURN_TO, url_for("index")))


def is_prod_build():
    return ".pr." not in get_host() and "cs61a" in get_host()


def get_hosted_app_name():
    return "sandbox" if is_prod_build() else f"sandbox-pr{get_host().split('.')[0]}"


def get_username():
    return (
        get_user()["email"].split("@")[0].replace(".", "-")
        if is_prod_build()
        else DEFAULT_USER
    )


def is_berkeley():
    return get_user()["email"].endswith("@berkeley.edu")


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

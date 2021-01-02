import os, shutil, subprocess, sys, yaml, socket
from flask import Flask, request, url_for, redirect
from werkzeug.security import gen_salt
from nginx_utils import Server, Location

from common.oauth_client import (
    create_oauth_client,
    is_staff,
    login,
    get_user,
)
from common.rpc.hosted import add_domain
from common.shell_utils import sh

HOSTNAME = "cs61a.org"
SANDBOX = f"sb.{HOSTNAME}" if HOSTNAME == "cs61a.org" else HOSTNAME
CODESERVER = f"ide.{HOSTNAME}" if HOSTNAME == "cs61a.org" else HOSTNAME

app = Flask(__name__)

create_oauth_client(app, "61a-sandbox")


@app.route("/")
def index():
    if not is_staff("cs61a"):
        return login()

    username = get_user()["email"].split("@")[0]

    html = '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/spcss@0.5.0">\n'
    html += "<h1>61A Sandbox IDE</h1>\n"
    html += f"Hi {get_user()['name'].split()[0]}! Your sandbox is "

    if not get_server_pid(username):
        html += "inactive.<br />"
        html += f"""<form action="{url_for('start')}" method="POST">
        <input type="hidden" name="username" value="{username}" />
        <input type="submit" value="Start Sandbox" />
        </form>"""
        return html

    config = get_config(username)

    html += "active.<br />"
    html += f"""<form action="https://{username}.{CODESERVER}/login", method="POST" target="_blank">
    <input type="hidden" name="base" value="" /><input type="hidden" name="password" value="{config['password']}" />
    <input type="submit" value="Open in New Tab" />
    </form><form action="{url_for('kill')}" method="POST">
    <input type="hidden" name="username" value="{username}" />
    <input type="submit" value="Kill Sandbox" />
    </form>"""

    return html


@app.route("/start", methods=["POST"])
def start():
    if not is_staff("cs61a"):
        return login()

    username = request.form.get("username")
    try:
        sh("id", "-u", username)
        user_exists = True
    except:
        user_exists = False

    if not user_exists:
        sh("useradd", "-b", "/save", "-m", username, "-s", "/bin/bash")
        if HOSTNAME == "cs61a.org":
            add_domain(name="sandbox", domain=f"{username}.{CODESERVER}")

    if not get_server_pid(username):
        port, passwd = get_open_port(), gen_salt(24)

        config = {
            "socket": f"/tmp/ide-{username}.sock",
            "auth": "password",
            "password": passwd,
            "home": f"https://{SANDBOX}",
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
                **{
                    "proxy_set_header Host": "$host",
                    "proxy_set_header Upgrade": "$http_upgrade",
                    "proxy_set_header Connection": "upgrade",
                    "proxy_set_header Accept-Encoding": "gzip",
                },
            ),
            server_name=f"{username}.{CODESERVER}",
            listen="8001",
            error_page=f"502 http://{SANDBOX}",
        )

        with open(f"/etc/nginx/sites-enabled/{username}.{CODESERVER}", "w") as f:
            f.write(str(conf))
        sh("nginx", "-s", "reload")

    if not os.path.exists(f"/save/{username}/berkeley-cs61a"):
        shutil.copytree(
            "/save/berkeley-cs61a", f"/save/{username}/berkeley-cs61a", symlinks=True
        )
        sh("chown", "-R", username, f"/save/{username}/berkeley-cs61a")

    return redirect(url_for("index"))


def get_open_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))

    s.listen(1)
    port = s.getsockname()[1]

    s.close()
    return port


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
    except:
        return False


@app.route("/kill", methods=["POST"])
def kill():
    if not is_staff("cs61a"):
        return login()

    username = request.form.get("username")
    pid = get_server_pid(username)

    if pid:
        sh("kill", pid.decode("utf-8")[:-1])
        sh("sleep", "2")  # give the server a couple of seconds to shutdown
    return redirect(url_for("index"))


def get_config(username):
    with open(f"/save/{username}/.code-server.yaml") as csc:
        data = yaml.load(csc)
    return data


try:
    sh("nginx", quiet=True)

    conf = Server(
        Location(
            "/",
            include="proxy_params",
            proxy_pass="http://127.0.0.1:14789",
        ),
        listen="8001",
        server_name=SANDBOX,
    )

    with open(f"/etc/nginx/sites-enabled/{SANDBOX}", "w") as f:
        f.write(str(conf))
except:
    pass  # another thread handled setup

sh("nginx", "-s", "reload")

if __name__ == "__main__":
    app.run()

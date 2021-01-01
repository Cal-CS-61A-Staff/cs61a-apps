import os, shutil
from flask import Flask, jsonify

from common.oauth_client import (
    create_oauth_client,
    is_staff,
    login,
)
from common.rpc.hosted import add_domain
from common.shell_utils import sh
from common.url_for import get_host

app = Flask(__name__)

def get_host_username():
    return get_host().split(".")[0]

@app.route("/")
def index():
    if not is_staff("cs61a"):
        return login()
    if get_host() == "sb.cs61a.org":
        return jsonify(success=True)
    
    username = get_host_username()
    user_exists = True
    try:
        sh("id", "-u", username)
    except:
        user_exists = False
    
    if not user_exists:
        sh("useradd", "-b", "/save", "-m", username)
        os.makedirs(f"/save/{username}/.config/code-server/")
        with open(f"/save/{username}/.config/code-server/config.yaml", "w") as csc:
            csc.write(f"socket: /save/{username}/.config/code-{username}.sock")
            csc.write("auth: none")
            
            # TODO: install extensions
    
    if not os.path.exists(f"/save/{username}/berkeley-cs61a"):
        shutil.copytree("/save/root/berkeley-cs61a", f"/save/{username}/berkeley-cs61a")
        sh("chown", "-R", username, f"/save/{username}/berkeley-cs61a")

    if not os.path.exists(f"/save/{username}/cs61a-apps"):
        shutil.copytree("/save/root/cs61a-apps", f"/save/{username}/cs61a-apps")
        sh("chown", "-R", username, f"/save/{username}/cs61a-apps")

@app.route()


if __name__ == "__main__":
    app.run()
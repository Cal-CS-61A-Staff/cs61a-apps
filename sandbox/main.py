import os
from base64 import b64decode
from functools import wraps
from os.path import abspath
from pathlib import Path
from sys import stderr
from typing import Optional

import requests
from flask import Flask, g, redirect, request, safe_join

from common.course_config import get_endpoint
from common.oauth_client import AUTHORIZED_ROLES, create_oauth_client, is_staff
from common.shell_utils import sh
from common.url_for import get_host, url_for
from sicp.build import get_hash, hash_all
from common.rpc.sandbox import get_server_hashes, run_incremental_build, update_file

app = Flask(__name__, static_folder="", static_url_path="")
if __name__ == "__main__":
    app.debug = True

WORKING_DIRECTORY = abspath("tmp") if app.debug else "/save"

create_oauth_client(app, "61a-sandbox")


class Failure(Exception):
    pass


def is_staff_userdata(userdata):
    try:
        endpoint = get_endpoint(course="cs61a")
        for participation in userdata["participations"]:
            if participation["role"] not in AUTHORIZED_ROLES:
                continue
            if participation["course"]["offering"] != endpoint:
                continue
            return True
        return False
    except Exception as e:
        # fail safe!
        print(e)
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
        if not is_staff_userdata(ret.json()["data"]):
            raise PermissionError
        return func(**kwargs)

    return decorated


def is_prod_build():
    return not app.debug and ".pr." not in get_host() and "cs61a" in get_host()


def get_working_directory():
    if is_prod_build():
        # TODO: check if user sandbox is provisioned
        return WORKING_DIRECTORY
    else:
        # Everyone shares the same working directory on dev / PR builds
        return WORKING_DIRECTORY


@app.route("/")
def index():
    if not is_staff("cs61a"):
        return redirect(url_for("login"))
    return "<code>Welcome to the sandbox!</code>"


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
            print("Symlinking:", target, symlink)
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
def run_incremental_build():
    os.chdir(get_working_directory())
    os.chdir("src")
    sh("make", "VIRTUAL_ENV=../env", "unreleased")


@get_server_hashes.bind(app)
@verifies_access_token
def get_server_hashes():
    base = get_working_directory()
    os.chdir(base)
    return hash_all()


if __name__ == "__main__":
    app.run()

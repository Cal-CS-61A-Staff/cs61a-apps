import os
from os import mkdir
from os.path import abspath
from subprocess import CalledProcessError

from flask import Flask

from common.rpc.buildserver_hosted_worker import build_worker_build
from common.rpc.secrets import get_secret, only
from common.shell_utils import sh

app = Flask(__name__)
if __name__ == "__main__":
    app.debug = True

APP = "website-base"
REPO_FOLDER = "/save/berkeley-cs61a"
REPO_PATH = "Cal-CS-61A-Staff/berkeley-cs61a"


def make(target):
    out = sh(
        "make",
        "--no-print-directory",
        "-C",
        "src",
        target,
        capture_output=True,
    )
    return out.decode("utf-8", "replace")


@build_worker_build.bind(app)
@only("buildserver", allow_staging=True)
def build_worker_build(pr_number: int, sha: str):
    if not os.path.exists(REPO_FOLDER):
        print("Cloning working copy of berkeley-cs61a")
        sh(
            "git",
            "clone",
            f"https://{get_secret(secret_name='GITHUB_ACCESS_TOKEN')}@github.com/{REPO_PATH}",
            REPO_FOLDER,
        )
    else:
        print("Folder", abspath(REPO_FOLDER), "already exists")

    # our working directory is not fixed, so we can only use absolute paths before this point
    os.chdir(REPO_FOLDER)

    # prepare working directory
    sh("git", "fetch", "origin", "--prune")
    sh("git", "checkout", "-f", sha)
    sh("git", "clean", "-fdx", "-e", ".cache", "-e", ".state", "-e", "env")

    # build repo
    logs = []
    mkdir("out")
    try:
        logs.append(make("all"))
        sh("cp", "-aT", "published", "out/released", capture_output=True)
        logs.append(make("unreleased"))
        sh("cp", "-aT", "published", "out/unreleased", capture_output=True)
    except CalledProcessError as e:
        logs.append(e.stdout.decode("utf-8", "replace"))
        logs.append(e.stderr.decode("utf-8", "replace"))
        return False, "".join(logs)

    # deploy to bucket
    bucket_id = APP if pr_number == 0 else f"{APP}-pr{pr_number}"
    bucket = f"gs://{bucket_id}.buckets.cs61a.org"
    try:
        sh("gsutil", "mb", "-b", "on", bucket)
    except CalledProcessError:
        # bucket already exists
        pass

    os.chdir("out")
    sh("gsutil", "-m", "rsync", "-dRc", ".", bucket)

    return True, "".join(logs)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True, threaded=False)

import os
from shutil import copytree, rmtree
from urllib.parse import urlparse

from app_config import App
from common.db import connect_db
from common.rpc.secrets import get_secret
from common.shell_utils import sh, tmp_directory


def gen_working_dir(app: App):
    return f"{app}_deploy_DO_NOT_USE"


def clone_commit(remote: str, sha: str, *, in_place=False):
    path = urlparse(remote).path

    def clone():
        sh("git", "init")
        sh(
            "git",
            "fetch",
            "--depth=1",
            f"https://{get_secret(secret_name='GITHUB_ACCESS_TOKEN')}@github.com{path}",
            sha,
        )
        sh("git", "checkout", "FETCH_HEAD")

    if in_place:
        clone()
    else:
        with tmp_directory(clean=True):
            clone()


def build(app: App, pr_number: int = 0):
    with tmp_directory():
        try:
            os.chdir(app.name)
        except FileNotFoundError:
            # app has been deleted in PR
            with connect_db() as db:
                db(
                    "DELETE FROM services WHERE app=%s AND pr_number=%s",
                    [app.name, pr_number],
                )
            return

        app_dir = app.name

        os.chdir("..")
        deploy_dir = gen_working_dir(app)

        copytree(app_dir, deploy_dir, dirs_exist_ok=True)

        os.chdir(deploy_dir)

        {
            "oh_queue": run_oh_queue_build,
            "create_react_app": run_create_react_app_build,
            "none": run_noop_build,
        }[app.config["build_type"]]()


def run_oh_queue_build():
    sh("python", "-m", "venv", "env")
    sh("env/bin/pip", "freeze")
    sh("env/bin/pip", "install", "-r", "requirements.txt")
    sh("npm", "install")
    sh("env/bin/python", "./manage.py", "build")


def run_create_react_app_build():
    sh("yarn")
    sh("yarn", "build")
    for dirpath, _, filenames in os.walk("."):
        dirnames = dirpath.split(os.sep)[1:]
        if not dirnames:
            for filename in filenames:
                os.remove(filename)
        elif dirnames[0] != "deploy":
            rmtree(dirpath)

    copytree("deploy", ".", dirs_exist_ok=True)
    rmtree("deploy")


def run_noop_build():
    pass


if __name__ == "__main__":
    with tmp_directory():
        run_create_react_app_build()

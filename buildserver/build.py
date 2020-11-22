import os
from shutil import copytree, rmtree
from subprocess import CalledProcessError
from urllib.parse import urlparse

from app_config import App
from common.db import connect_db
from common.rpc.secrets import get_secret
from common.shell_utils import clean_all_except, sh, tmp_directory


def gen_working_dir(app: App):
    return f"{app}_working_DO_NOT_USE"


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
                if pr_number == 0:
                    db("DELETE FROM apps WHERE app=%s", [app.name])
            return

        app_dir = app.name

        os.chdir("..")
        working_dir = gen_working_dir(app)

        copytree(app_dir, working_dir, dirs_exist_ok=True, symlinks=False)

        os.chdir(working_dir)

        {
            "oh_queue": run_oh_queue_build,
            "create_react_app": run_create_react_app_build,
            "webpack": run_webpack_build,
            "61a_website": run_61a_website_build,
            "hugo": run_hugo_build,
            "none": run_noop_build,
        }[app.config["build_type"]]()

        os.chdir("..")


def run_oh_queue_build():
    sh("python", "-m", "venv", "env")
    sh("env/bin/pip", "freeze")
    sh("env/bin/pip", "install", "-r", "requirements.txt")
    sh("yarn")
    sh("env/bin/python", "./manage.py", "build")


def run_create_react_app_build():
    sh("yarn")
    sh("yarn", "build")
    clean_all_except(["deploy"])
    copytree("deploy", ".", dirs_exist_ok=True)
    rmtree("deploy")


def run_webpack_build():
    sh("yarn")
    sh("yarn", "run", "webpack")
    sh("rm", "-rf", "node_modules")


def run_61a_website_build():
    env = dict(
        CLOUD_STORAGE_BUCKET="website-pdf-cache.buckets.cs61a.org", VIRTUAL_ENV="../env"
    )

    sh("python", "-m", "venv", "env", "--system-site-packages")

    # install dependencies
    sh("make", "-C", "src", "check-env", env=env)

    def build(target):
        # need to re-run make for stupid reasons
        num_iterations = 3
        for i in range(num_iterations):
            is_last_iteration = i == num_iterations - 1
            parallel_args = ["-j1"] if is_last_iteration else ["-j4"]
            sh(
                "make",
                "--no-print-directory",
                "-C",
                "src",
                "BUILDTYPE=pull",
                target,
                f"BUILDPASS={i+1}",
                *parallel_args,
                env=env,
            )

    build("all")
    copytree("published", "released", dirs_exist_ok=True)
    build("unreleased")
    copytree("published", "unreleased", dirs_exist_ok=True)
    clean_all_except(["released", "unreleased"])


def run_hugo_build():
    sh("hugo")
    clean_all_except(["public"])
    copytree("public", ".", dirs_exist_ok=True)
    rmtree("public")


def run_noop_build():
    pass


if __name__ == "__main__":
    with tmp_directory():
        run_61a_website_build()

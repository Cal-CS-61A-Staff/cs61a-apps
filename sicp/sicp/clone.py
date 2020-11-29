import click

from sicp.common.shell_utils import sh
import os


@click.command()
@click.argument("repo")
@click.argument("dest", default="")
def clone(repo, dest):
    """Clone REPO to DEST.

    REPO is the name of the 61a repo to set up.
    Currently, "apps" and "cs61a" are supported.
    By default, DEST is set to the name of REPO.
    """
    if repo == "apps":
        run_apps_clone(dest if dest else "cs61a-apps")
    elif repo == "cs61a":
        run_61a_clone(dest if dest else "berkeley-cs61a")
    else:
        click.echo("No need to use sicp for that! Just git clone.", err=True)


def run_apps_clone(dir):
    print("========== Cloning cs61a-apps ==========")
    sh("git", "clone", "https://github.com/Cal-CS-61A-Staff/cs61a-apps", dir)

    print("====== Installing Black & Prettier =====")
    if "black" not in sh("pip3", "list", quiet=True).decode("utf-8"):
        sh("pip3", "install", "black")
    if "prettier" not in sh("npm", "list", "-g", quiet=True).decode("utf-8"):
        sh("npm", "install", "-g", "prettier")

    print("========== Linking .githooks ===========")
    os.chdir(dir)
    sh("chmod", "+x", ".githooks/pre-commit")
    sh("git", "config", "core.hooksPath", ".githooks")

    print("================ Done! =================")


def run_61a_clone(dir):
    print("======== Cloning berkeley-cs61a ========")
    sh("git", "clone", "https://github.com/Cal-CS-61A-Staff/berkeley-cs61a", dir)

    print("================ Done! =================")

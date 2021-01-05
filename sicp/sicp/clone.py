import click

from common.shell_utils import sh
import os, sys
from subprocess import CalledProcessError

HTTPS = "https://github.com/"
SSH = "git@github.com:"


@click.command()
@click.argument("repo")
@click.argument("dest", default="")
@click.option("--ssh", is_flag=True)
def clone(repo, dest, ssh):
    """Clone REPO into DEST.

    REPO is the name of the 61a repo to set up.
    Currently, "apps" and "cs61a" are supported.
    By default, DEST is set to the name of REPO.
    If you want to clone over SSH, use the SSH
    option.
    """
    if repo == "apps":
        run_apps_clone(dest if dest else "cs61a-apps", SSH if ssh else HTTPS)
    elif repo == "cs61a":
        run_61a_clone(dest if dest else "berkeley-cs61a", SSH if ssh else HTTPS)
    else:
        click.echo("No need to use sicp for that! Just git clone.", err=True)


def run_apps_clone(dir, protocol):
    print("========== Cloning cs61a-apps ==========")
    sh("git", "clone", f"{protocol}Cal-CS-61A-Staff/cs61a-apps", dir)

    print("========== Linking .githooks ===========")
    os.chdir(dir)
    sh("chmod", "+x", ".githooks/pre-commit")
    sh("git", "config", "core.hooksPath", ".githooks")

    print("====== Installing Black & Prettier =====")
    if "black" not in sh("pip3", "list", quiet=True).decode("utf-8"):
        sh("pip3", "install", "black")
    try:
        if "prettier" not in sh("npm", "list", "-g", quiet=True).decode("utf-8"):
            sh("sudo", "npm", "install", "-g", "prettier")
    except CalledProcessError:
        print(
            "Failed to install prettier globally as needed! "
            + "Make sure you have npm installed and have sudo privileges.",
            file=sys.stderr,
        )

    print("================ Done! =================")


def run_61a_clone(dir, protocol):
    print("======== Cloning berkeley-cs61a ========")
    sh("git", "clone", f"{protocol}Cal-CS-61A-Staff/berkeley-cs61a", dir)

    print("================ Done! =================")

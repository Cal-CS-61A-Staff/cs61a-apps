from sicp.common.shell_utils import sh
import os


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

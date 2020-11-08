import os
from os import chdir, mkdir
from os.path import isdir
from shutil import copyfile, copytree

from github import Github

from app_config import App
from build import clone_commit
from common.rpc.secrets import get_secret
from common.shell_utils import tmp_directory


def load_dependencies(app: App):
    g = Github(get_secret(secret_name="GITHUB_ACCESS_TOKEN"))

    with tmp_directory():
        for dependency in app.config["dependencies"]:
            folder_name = dependency["repo"].replace("/", "-")
            if not isdir(folder_name):
                # dependency is not already loaded
                repo = g.get_repo(dependency["repo"])
                sha = repo.get_branch(repo.default_branch).commit.sha
                mkdir(folder_name)
                chdir(folder_name)
                clone_commit(repo.clone_url, sha, in_place=True)
                chdir("..")
            try:
                copytree(
                    os.path.join(folder_name, dependency["src"]),
                    os.path.join(app.name, dependency["dest"]),
                    symlinks=True,
                    dirs_exist_ok=True,
                )
            except NotADirectoryError:
                copyfile(
                    os.path.join(folder_name, dependency["src"]),
                    os.path.join(app.name, dependency["dest"]),
                )

import os
from os import chdir, mkdir
from os.path import isdir
from shutil import copyfile, copytree

from github import Github
from github.Repository import Repository

from app_config import App
from build import clone_commit, gen_working_dir
from common.rpc.secrets import get_secret
from common.shell_utils import tmp_directory


def load_dependencies(app: App, sha: str, repo: Repository):
    g = Github(get_secret(secret_name="GITHUB_ACCESS_TOKEN"))

    def clone_repo(repo_str: str):
        cloned_repo = g.get_repo(repo_str)
        cloned_sha = (
            sha
            if cloned_repo.full_name == repo.full_name
            else cloned_repo.get_branch(cloned_repo.default_branch).commit.sha
        )
        clone_commit(cloned_repo.clone_url, cloned_sha, in_place=True)

    with tmp_directory():
        for dependency in app.config["dependencies"]:
            folder_name = dependency["repo"].replace("/", "-")
            if not isdir(folder_name):
                # dependency is not already loaded
                mkdir(folder_name)
                chdir(folder_name)
                clone_repo(dependency["repo"])
                chdir("..")
            try:
                copytree(
                    os.path.join(folder_name, dependency["src"]),
                    os.path.join(app.name, dependency["dest"]),
                    symlinks=False,
                    dirs_exist_ok=True,
                )
            except NotADirectoryError:
                copyfile(
                    os.path.join(folder_name, dependency["src"]),
                    os.path.join(app.name, dependency["dest"]),
                )
        if app.config["repo"]:
            working_dir = gen_working_dir(app)
            mkdir(working_dir)
            chdir(working_dir)
            clone_repo(app.config["repo"])
            chdir("..")

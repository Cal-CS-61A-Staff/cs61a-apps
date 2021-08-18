import fnmatch
from typing import Dict, Iterable, Set, Union

import yaml
from github.File import File
from github.Repository import Repository

from app_config import App
from github_utils import get_github
from conf import GITHUB_REPO


def get_all_apps(repo: Repository, sha: str) -> Dict[str, App]:
    base_repo = get_github().get_repo(GITHUB_REPO)
    base_sha = (
        sha
        if repo.full_name == GITHUB_REPO
        else base_repo.get_branch(base_repo.default_branch).commit.sha
    )
    return {
        target: App(target, config)
        for target, config in yaml.safe_load(
            base_repo.get_contents("targets.yaml", base_sha).decoded_content
        ).items()
    }


def determine_targets(
    repo: Repository, sha: str, files: Iterable[Union[File, str]]
) -> Set[str]:
    apps = get_all_apps(repo, sha)

    # todo: target detection when we modify targets.yaml itself
    modified_targets = []

    if repo.full_name == GITHUB_REPO:
        modified_paths = []
        for file in files:
            if isinstance(file, str):
                modified_paths.append(file)
            else:
                modified_paths.append(file.filename)
                modified_paths.append(file.previous_filename)

        for app_name, app in apps.items():
            if any(
                fnmatch.filter(modified_paths, match) for match in app.config["match"]
            ):
                modified_targets.append(app_name)

    for app_name, app in apps.items():
        if app.config["repo"] == repo.full_name:
            modified_targets.append(app_name)

    return set(modified_targets)

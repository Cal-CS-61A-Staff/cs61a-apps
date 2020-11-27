from typing import Iterable, Optional, Union

from github.File import File
from github.PullRequest import PullRequest
from github.Repository import Repository

from app_config import App, CLOUD_RUN_DEPLOY_TYPES
from build import build, clone_commit
from dependency_loader import load_dependencies
from deploy import deploy_commit, update_service_routes
from external_repo_utils import update_config
from github_utils import (
    set_pr_comment,
)
from scheduling import BuildStatus, enqueue_builds, pack, report_build_status, unpack
from external_build import run_highcpu_build
from target_determinator import determine_targets


def land_app(
    app: App,
    pr_number: int,
    sha: str,
    repo: Repository,
):
    update_config(app, pr_number)
    if app.config["build_image"]:
        run_highcpu_build(app, pr_number, sha, repo)
    else:
        land_app_worker(app, pr_number, sha, repo)


def land_app_worker(
    app: App,
    pr_number: int,
    sha: str,
    repo: Repository,
):
    load_dependencies(app, sha, repo)
    build(app, pr_number)
    deploy_commit(app, pr_number)


def land_commit(
    sha: str,
    repo: Repository,
    base_repo: Repository,
    pr: Optional[PullRequest],
    files: Iterable[Union[File, str]],
    *,
    target_app: Optional[str] = None,
):
    """
    :param sha: The hash of the commit we are building
    :param repo: The repo containing the above commit
    :param base_repo: The *base* cs61a-apps repo containing the deploy.yaml config
    :param pr: The PR made to trigger the build, if any
    :param files: Files changed in the commit, used for target determination
    :param target_app: App to rebuild, if not all
    """
    try:
        repo.get_commit(sha).create_status(
            "pending",
            "https://logs.cs61a.org/service/buildserver",
            "Pusher is rebuilding all modified services",
            "Pusher",
        )
        if target_app:
            targets = [target_app]
        else:
            targets = determine_targets(
                repo, files if repo.full_name == base_repo.full_name else []
            )
        target_list = "\n".join(f" * {target}" for target in targets)
        set_pr_comment(
            f"Building commit: {sha}. View logs at [logs.cs61a.org](https://logs.cs61a.org).\n"
            f"Targets: \n{target_list}",
            pr,
        )
        grouped_targets = enqueue_builds(targets, pr.number, pack(repo.clone_url, sha))
        for packed_ref, targets in grouped_targets.items():
            repo_clone_url, sha = unpack(packed_ref)
            # If the commit is made on the base repo, take the config from the current commit.
            # Otherwise, retrieve it from master
            clone_commit(
                base_repo.clone_url,
                sha
                if repo_clone_url == base_repo.clone_url
                else base_repo.get_branch(base_repo.default_branch).commit.sha,
            )
            apps = [App(target) for target in targets]
            for app in apps:
                try:
                    land_app(app, pr.number if pr else 0, sha, repo)
                except:
                    report_build_status(
                        app.name,
                        pr.number,
                        pack(repo.clone_url, sha),
                        BuildStatus.failure,
                    )
                else:
                    report_build_status(
                        app.name,
                        pr.number,
                        pack(repo.clone_url, sha),
                        BuildStatus.success,
                    )
            update_service_routes(apps, pr.number if pr else 0)

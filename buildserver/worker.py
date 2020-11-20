from typing import Iterable, Optional, Union

from github.File import File
from github.PullRequest import PullRequest
from github.Repository import Repository

from app_config import App, CLOUD_RUN_DEPLOY_TYPES
from build import build, clone_commit
from dependency_loader import load_dependencies
from deploy import deploy_commit, update_service_routes
from external_repo_utils import update_config
from github_utils import set_pr_comment
from lock import service_lock
from target_determinator import determine_targets


def land_app(
    app: App,
    pr_number: int,
    sha: str,
    repo: Repository,
):
    with service_lock(app, pr_number):
        load_dependencies(app, sha, repo)
        update_config(app, pr_number)
        build(app, pr_number)
        deploy_commit(app, pr_number)


def land_commit(
    sha: str,
    repo: Repository,
    base_repo: Repository,
    pr: Optional[PullRequest],
    files: Iterable[Union[File, str]],
    target_app: str,
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
        # If the commit is made on the base repo, take the config from the current commit.
        # Otherwise, retrieve it from master
        clone_commit(
            base_repo.clone_url,
            sha
            if repo.full_name == base_repo.full_name
            else base_repo.get_branch(base_repo.default_branch).commit.sha,
        )
        apps = [App(target) for target in targets]
        for app in apps:
            land_app(app, pr.number if pr else 0, sha, repo)
        update_service_routes(apps, pr.number if pr else 0)
    except Exception as e:
        repo.get_commit(sha).create_status(
            "failure",
            "https://logs.cs61a.org/service/buildserver",
            "Pusher failed to rebuild all modified services",
            "Pusher",
        )
        set_pr_comment(
            "Builds failed. View logs at [logs.cs61a.org](https://logs.cs61a.org).", pr
        )
        raise
    else:
        repo.get_commit(sha).create_status(
            "success",
            "https://logs.cs61a.org/service/buildserver",
            "All modified services rebuilt!",
            "Pusher",
        )
        web_app_names = [
            app.name
            for app in apps
            if app.config["deploy_type"] in CLOUD_RUN_DEPLOY_TYPES
        ] + [consumer for app in apps for consumer in app.config["static_consumers"]]
        pr_builds_text = (
            "\n\nDeployed PR builds are available at: \n"
            + "\n".join(
                f" * [{pr.number}.{app_name}.pr.cs61a.org](https://{pr.number}.{app_name}.pr.cs61a.org)"
                for app_name in web_app_names
            )
            if web_app_names and pr is not None
            else ""
        )
        if pr is not None:
            pypi_apps = [app for app in apps if app.config["deploy_type"] == "pypi"]
            pypi_app_details = [
                (app.config["package_name"], app.deployed_pypi_version)
                for app in pypi_apps
            ]
            if pypi_apps:
                pr_builds_text += (
                    "\n\nPre-release builds of PyPI packages are available at: \n"
                ) + "\n".join(
                    f" * [pypi.org/project/{package_name}/{version}]"
                    f"(https://pypi.org/project/{package_name}/{version}/)"
                    for package_name, version in pypi_app_details
                )
        set_pr_comment(
            "Builds completed! View logs at [logs.cs61a.org](https://logs.cs61a.org)."
            + pr_builds_text,
            pr,
        )

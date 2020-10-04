from typing import Iterable, Optional, Union

from github.File import File
from github.PullRequest import PullRequest
from github.Repository import Repository

from app_config import App, WEB_DEPLOY_TYPES
from build import build, clone_commit
from deploy import deploy_commit, update_service_routes
from github_utils import set_pr_comment
from lock import service_lock
from target_determinator import determine_targets


def land_app(app: App, pr_number: int = 0):
    with service_lock(app, pr_number):
        build(app, pr_number)
        deploy_commit(app, pr_number)


def land_commit(
    sha: str,
    repo: Repository,
    pr: Optional[PullRequest],
    files: Iterable[Union[File, str]],
):
    try:
        repo.get_commit(sha).create_status(
            "pending",
            "https://buildserver.experiments.cs61a.org",
            "Pusher is rebuilding all modified services",
            "Pusher",
        )
        targets = determine_targets(files)
        target_list = "\n".join(f" * {target}" for target in targets)
        set_pr_comment(
            f"Building commit: {sha}. View logs at [logs.cs61a.org](https://logs.cs61a.org).\n"
            f"Targets: \n{target_list}",
            pr,
        )
        clone_commit(repo.clone_url, sha)
        apps = [App(target) for target in targets]
        for app in apps:
            land_app(app, pr.number if pr else 0)
        update_service_routes(apps, pr.number if pr else 0)
    except Exception as e:
        repo.get_commit(sha).create_status(
            "failure",
            "https://buildserver.cs61a.org",
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
            "https://buildserver.cs61a.org",
            "All modified services rebuilt!",
            "Pusher",
        )
        web_apps = [
            app for app in apps if app.config["deploy_type"] in WEB_DEPLOY_TYPES
        ]
        pr_builds_text = (
            "\n\nDeployed PR builds are available at: \n"
            + "\n".join(
                f" * [{pr.number}.{app.name}.pr.cs61a.org](https://{pr.number}.{app.name}.pr.cs61a.org)"
                for app in web_apps
            )
            if web_apps and pr is not None
            else ""
        )
        set_pr_comment(
            "Builds completed! View logs at [logs.cs61a.org](https://logs.cs61a.org)."
            + pr_builds_text,
            pr,
        )

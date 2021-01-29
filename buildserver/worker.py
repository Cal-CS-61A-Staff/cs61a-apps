import tempfile
import traceback
from sys import stderr, stdout
from typing import Iterable, Optional, Union

from github.File import File
from github.PullRequest import PullRequest
from github.Repository import Repository

from app_config import App
from build import build, clone_commit
from common.db import connect_db
from common.rpc.buildserver import clear_queue
from common.shell_utils import redirect_descriptor
from dependency_loader import load_dependencies
from deploy import deploy_commit
from external_build import run_highcpu_build
from external_repo_utils import update_config
from github_utils import (
    BuildStatus,
    pack,
    unpack,
)
from scheduling import enqueue_builds, report_build_status
from service_management import get_pr_subdomains, update_service_routes
from target_determinator import determine_targets


def land_app(
    app: App,
    pr_number: int,
    sha: str,
    repo: Repository,
):
    if app.config is None:
        delete_app(app, pr_number)
        return

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
    build(app)
    deploy_commit(app, pr_number)


def delete_app(app: App, pr_number: int):
    with connect_db() as db:
        db(
            "DELETE FROM services WHERE app=%s AND pr_number=%s",
            [app.name, pr_number],
        )
        if pr_number == 0:
            db("DELETE FROM apps WHERE app=%s", [app.name])


def land_commit(
    sha: str,
    repo: Repository,
    base_repo: Repository,
    pr: Optional[PullRequest],
    files: Iterable[Union[File, str]],
    *,
    target_app: Optional[str] = None,
    dequeue_only=False,
):
    """
    :param sha: The hash of the commit we are building
    :param repo: The repo containing the above commit
    :param base_repo: The *base* cs61a-apps repo containing the deploy.yaml config
    :param pr: The PR made to trigger the build, if any
    :param files: Files changed in the commit, used for target determination
    :param target_app: App to rebuild, if not all
    :param dequeue_only: Only pop targets off the queue, do not build any new targets
    """
    if dequeue_only:
        targets = []
    elif target_app:
        targets = [target_app]
    else:
        targets = determine_targets(
            repo, files if repo.full_name == base_repo.full_name else []
        )
    pr_number = pr.number if pr else 0
    grouped_targets = enqueue_builds(targets, pr_number, pack(repo.clone_url, sha))
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
            with tempfile.TemporaryFile("w+") as logs:
                try:
                    with redirect_descriptor(stdout, logs), redirect_descriptor(
                        stderr, logs
                    ):
                        land_app(app, pr_number, sha, repo)
                except:
                    traceback.print_exc(file=logs)
                    logs.seek(0)
                    report_build_status(
                        app.name,
                        pr_number,
                        pack(repo.clone_url, sha),
                        BuildStatus.failure,
                        None,
                        logs.read(),
                        private=repo.full_name == base_repo.full_name,
                    )
                else:
                    logs.seek(0)
                    report_build_status(
                        app.name,
                        pr_number,
                        pack(repo.clone_url, sha),
                        BuildStatus.success,
                        None
                        if app.config is None
                        else ",".join(
                            hostname.to_str()
                            for hostname in get_pr_subdomains(app, pr_number)
                        ),
                        logs.read(),
                        private=repo.full_name == base_repo.full_name,
                    )

            if app.config is not None:
                update_service_routes([app], pr_number)
    if grouped_targets:
        # because we ran a build, we need to clear the queue of anyone we blocked
        # we run this in a new worker to avoid timing out
        clear_queue(repo=repo.full_name, pr_number=pr_number, noreply=True)

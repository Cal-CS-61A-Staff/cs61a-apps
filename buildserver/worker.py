import tempfile
import traceback
from sys import stderr, stdout
from typing import Callable, Iterable, Optional, Union

from github import Github
from github.File import File
from github.PullRequest import PullRequest
from github.Repository import Repository

from app_config import App
from build import build, clone_commit
from common.db import connect_db
from common.rpc.buildserver import clear_queue
from common.rpc.buildserver_hosted_worker import build_worker_build
from common.shell_utils import redirect_descriptor
from dependency_loader import load_dependencies
from deploy import deploy_commit
from external_build import run_highcpu_build
from external_repo_utils import update_config
from github_utils import (
    BuildStatus,
    get_github,
    pack,
    repo_name_from_packed_ref,
    unpack,
)
from scheduling import (
    TARGETS_BUILT_ON_WORKER,
    dequeue_builds,
    enqueue_builds,
    report_build_status,
)
from service_management import get_pr_subdomains, update_service_routes
from target_determinator import determine_targets, get_all_apps


def land_app(app: App, pr_number: int, sha: str, repo: Repository, clone: Callable):
    if app.config is None:
        delete_app(app, pr_number)
        return

    update_config(app, pr_number)

    if app.name in TARGETS_BUILT_ON_WORKER:
        if repo.full_name != app.config.get("repo", repo.full_name):
            # the worker does not do dependency resolution, so we must
            # give it the hash for the correct repo
            app_repo = get_github().get_repo(app.config["repo"])
            worker_sha = app_repo.get_branch(app_repo.default_branch).commit.sha
        else:
            worker_sha = sha
        success, logs = build_worker_build(
            sha=worker_sha, pr_number=pr_number, timeout=20 * 60
        )
        print(logs)
        if not success:
            raise Exception("Build failed")
    else:
        # We defer cloning to here, so that if we're building on the worker / not building at all,
        # we don't have to do a slow clone
        if app.config["repo"]:
            load_dependencies(app, sha, repo)
        else:
            clone()

        build(app)
        deploy_commit(app, pr_number)


def delete_app(app: App, pr_number: int):
    with connect_db() as db:
        db(
            "DELETE FROM services WHERE app=%s AND pr_number=%s",
            [app.name, pr_number],
        )


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
    :param dequeue_only: Only pop targets off the queue, do not build any new targets
    """
    if target_app:
        targets = [target_app]
    else:
        targets = determine_targets(
            repo, sha, files if repo.full_name == base_repo.full_name else []
        )
    pr_number = pr.number if pr else 0
    enqueue_builds(targets, pr_number, pack(repo.clone_url, sha))
    dequeue_and_build(base_repo)


def dequeue_and_build(base_repo: Repository):
    grouped_targets = dequeue_builds()
    for packed_ref, targets in grouped_targets.items():
        repo_clone_url, sha = unpack(packed_ref)
        repo_name = repo_name_from_packed_ref(packed_ref)
        repo = get_github().get_repo(repo_name)
        cloned = False

        def clone():
            nonlocal cloned
            if cloned:
                return

            cloned = True
            # If the commit is made on the base repo, take the config from the current commit.
            # Otherwise, retrieve it from master
            clone_commit(
                base_repo.clone_url,
                sha
                if repo_clone_url == base_repo.clone_url
                else base_repo.get_branch(base_repo.default_branch).commit.sha,
            )

        all_apps = get_all_apps(repo, sha)
        for app_name, pr_number in targets:
            app = all_apps.get(app_name, App(app_name, None))
            with tempfile.TemporaryFile("w+") as logs:
                try:
                    with redirect_descriptor(stdout, logs), redirect_descriptor(
                        stderr, logs
                    ):
                        land_app(app, pr_number, sha, repo, clone)
                    if app.config is not None:
                        update_service_routes([app], pr_number)
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

    if grouped_targets:
        # because we ran a build, we need to clear the queue of anyone we blocked
        # we run this in a new worker to avoid timing out
        clear_queue(noreply=True)

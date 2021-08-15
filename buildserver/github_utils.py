from enum import Enum, unique
from typing import Optional
from urllib.parse import urlparse

from github import Github
from github.PullRequest import PullRequest

from common.db import connect_db
from common.rpc.secrets import get_secret
from common.url_for import url_for
from env import GITHUB_BOT_USER
from target_determinator import determine_targets


def get_github():
    return Github(get_secret(secret_name="GITHUB_ACCESS_TOKEN"))


def repo_name_from_packed_ref(packed_ref):
    repo_url, _ = unpack(packed_ref)
    return urlparse(repo_url).path.split(".")[0][1:]  # This is awful ... but it works


def update_status(packed_ref: str, pr_number: int):
    g = get_github()
    repo_url, sha = unpack(packed_ref)
    repo_name = repo_name_from_packed_ref(packed_ref)
    repo = g.get_repo(repo_name)

    # First we will update the commit-specific status indicator
    with connect_db() as db:
        statuses = db(
            "SELECT app, status FROM builds WHERE packed_ref=%s", [packed_ref]
        ).fetchall()
    statuses = [(app, BuildStatus(status)) for app, status in statuses]
    if all(status == BuildStatus.success for _, status in statuses):
        repo.get_commit(sha).create_status(
            "success",
            "https://logs.cs61a.org/service/buildserver",
            "All modified services built!",
            "Pusher",
        )
    elif any(status == BuildStatus.failure for _, status in statuses):
        repo.get_commit(sha).create_status(
            "failure",
            "https://logs.cs61a.org/service/buildserver",
            "Pusher failed to build a modified service",
            "Pusher",
        )
    elif all(
        status in (BuildStatus.building, BuildStatus.queued) for _, status in statuses
    ):
        repo.get_commit(sha).create_status(
            "pending",
            "https://logs.cs61a.org/service/buildserver",
            "Pusher is building all modified services",
            "Pusher",
        )
    else:
        # There are no failures, but not everything is building / built
        repo.get_commit(sha).create_status(
            "pending",
            "https://logs.cs61a.org/service/buildserver",
            "You must build all modified apps before merging",
            "Pusher",
        )

    if pr_number == 0:
        return

    pr = repo.get_pull(pr_number)
    # Now we will update the PR comment, looking at builds for all packed_refs in the PR
    apps = determine_targets(repo, pr.get_files())
    success = []
    failure = []
    running = []
    queued = []
    triggerable = []
    with connect_db() as db:
        for app in apps:
            successful_build = db(
                "SELECT url, log_url, unix, packed_ref FROM builds WHERE app=%s AND pr_number=%s AND status='success' ORDER BY unix DESC LIMIT 1",
                [app, pr_number],
            ).fetchone()
            if successful_build:
                url, log_url, success_unix, packed_ref = successful_build
                _, sha = unpack(packed_ref)
                if url:
                    for link in url.split(","):
                        success.append((app, link, sha, log_url))
                else:
                    success.append((app, None, sha, log_url))

            failed_build = db(
                "SELECT unix, log_url, packed_ref FROM builds WHERE app=%s AND pr_number=%s AND status='failure' ORDER BY unix DESC LIMIT 1",
                [app, pr_number],
            ).fetchone()
            if failed_build:
                unix, log_url, packed_ref = failed_build
                if not successful_build or success_unix < unix:
                    _, sha = unpack(packed_ref)
                    failure.append((app, sha, log_url))

            running_build = db(
                "SELECT packed_ref FROM builds WHERE app=%s AND pr_number=%s AND status='building'",
                [app, pr_number],
            ).fetchone()
            if running_build:
                [packed_ref] = running_build
                _, sha = unpack(packed_ref)
                running.append((app, sha))

            queued_build = db(
                "SELECT packed_ref FROM builds WHERE app=%s AND pr_number=%s AND status='queued'",
                [app, pr_number],
            ).fetchone()
            if queued_build:
                [packed_ref] = queued_build
                _, sha = unpack(packed_ref)
                queued.append((app, sha))

            latest_commit_build = db(
                "SELECT * FROM builds WHERE app=%s AND pr_number=%s AND packed_ref=%s AND status!='pushed'",
                [app, pr_number, pack(repo_url, pr.head.sha)],
            ).fetchone()
            if not latest_commit_build:
                triggerable.append(app)

    if repo.name == "berkeley-cs61a":
        message = f"## Build Status ([pr/{pr_number}]({pr.html_url}))\n\n"
    elif repo.name == "cs61a-apps":
        message = f"## Build Status ([apps/{pr_number}]({pr.html_url}))\n\n"
    else:
        message = f"## Build Status (#{pr_number})\n\n"

    if success:
        message += (
            "**Successful Builds**\n"
            + "\n".join(
                f" - [{host}](https://{host}) ({sha}) [[logs]({log_url})]"
                if host
                else f" - `{app}` ({sha}) [[logs]({log_url})]"
                for app, host, sha, log_url in success
            )
            + "\n\n"
        )

    if failure:
        message += (
            "**Failed Builds**\n"
            + "\n".join(
                f" - `{app}` ({sha}) [[logs]({log_url})]"
                for app, sha, log_url in failure
            )
            + "\n\n"
        )

    if running:
        message += (
            "**Running Builds**\n"
            + "\n".join(f" - `{app}` ({sha})" for app, sha in running)
            + "\n\n"
        )

    if queued:
        message += (
            "**Queued Builds**\n"
            + "\n".join(f" - `{app}` ({sha})" for app, sha in queued)
            + "\n\n"
        )

    if (success or failure or running or queued) and triggerable:
        message += "-----\n"

    if triggerable:
        message += (
            f"**[Click here]({url_for('trigger_build', pr_number=pr.number)})** to trigger all builds "
            f"for the most recent commit ({pr.head.sha})\n\n"
            "Or trigger builds individually:\n"
        ) + "\n".join(
            f" - [Click here]({url_for('trigger_build', pr_number=pr.number, app=app)}) "
            f"to build `{app}` at the most recent commit ({pr.head.sha})"
            for app in triggerable
        )

    set_pr_comment(message, pr)


def set_pr_comment(text: str, pr: Optional[PullRequest]):
    if pr is None:
        return
    comments = pr.get_issue_comments()
    for comment in comments:
        if comment.user.login == GITHUB_BOT_USER:
            comment.edit(text)
            comment.update()
            break
    else:
        pr.create_issue_comment(text)


def pack(clone_url: str, sha: str) -> str:
    """
    Pack the source for a commit into a single str
    """
    return clone_url + "|" + sha


def unpack(packed_ref: str):
    return packed_ref.split("|")


@unique
class BuildStatus(Enum):
    pushed = "pushed"
    queued = "queued"
    building = "building"
    failure = "failure"
    success = "success"

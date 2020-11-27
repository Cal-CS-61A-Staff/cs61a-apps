from typing import Optional

from github.PullRequest import PullRequest

from common.db import connect_db
from env import GITHUB_BOT_USER
from scheduling import BuildStatus


def update_status(packed_ref: str, pr_number: int):
    with connect_db() as db:
        statuses = db("SELECT app, status FROM builds WHERE packed_ref=%s", [packed_ref]).fetchall()
    statuses = [(app, BuildStatus(status)) for app, status in statuses]
    if all(status == BuildStatus.success for _, status in statuses):
        # TODO success message
        ...
    elif any(status == BuildStatus.failure for _, status in statuses):
        # TODO failure message
        ...
    elif all(status == BuildStatus.pushed):
        # TODO pending message
        ...


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

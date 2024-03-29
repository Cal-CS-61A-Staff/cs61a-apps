import hmac

from flask import Flask, abort, redirect, request
from github import Github

import api
from common.db import connect_db
from common.html import html
from common.oauth_client import create_oauth_client, get_user, is_staff, login
from common.rpc.auth import is_admin
from common.rpc.buildserver import (
    clear_queue,
    deploy_prod_app_sync,
    get_base_hostname,
    trigger_build_sync,
)
from common.rpc.secrets import get_secret, only, validates_master_secret
from common.url_for import url_for
from conf import GITHUB_REPO
from github_utils import BuildStatus, get_github, pack, set_pr_comment
from rebuilder import create_rebuilder
from scheduling import report_build_status
from service_management import delete_unused_services
from target_determinator import determine_targets
from worker import dequeue_and_build, land_commit

DO_NOT_BUILD = "DO NOT BUILD"

app = Flask(__name__)
if __name__ == "__main__":
    app.debug = True

create_oauth_client(app, "61a-buildserver")
create_rebuilder(app)

with connect_db() as db:
    db(
        """CREATE TABLE IF NOT EXISTS services (
    app varchar(128),
    pr_number int,
    locked boolean,
    is_web_service boolean
)
"""
    )
    db(
        """CREATE TABLE IF NOT EXISTS apps (
    app varchar(128),
    repo varchar(128),
    autobuild boolean
)"""
    )
    db(
        """CREATE TABLE IF NOT EXISTS mysql_users (
    app varchar(128),
    mysql_pw varchar(128)
)"""
    )


def deploy_prod_app_description(app):
    if app == "website-base":
        return "<p>Redeploy cs61a.org</p>"
    return ""


@app.route("/")
def index():
    if not is_staff("cs61a"):
        return login()
    email = get_user()["email"]
    if not is_admin(course="cs61a", email=email):
        abort(401)
    with connect_db() as db:
        apps = db("SELECT app FROM services WHERE pr_number=0", []).fetchall()
        pr_apps = db(
            "SELECT app, pr_number FROM services WHERE pr_number>0 ORDER BY pr_number DESC",
            [],
        ).fetchall()
    return html(
        f"""
        This service manages the deployment of the 61A website and various apps.
        {"".join(f'''
        <form action="/deploy_prod_app">
            {deploy_prod_app_description(app)}
            <input type="submit" name="app" value="{app}" />
        </form>
        ''' for [app] in apps)}
        {"".join(f'''
        <form action="/trigger_build">
            <input type="hidden" name="app" value="{app}" />
            <input type="hidden" name="pr_number" value="{pr_number}" />
            <input type="submit" value="{app + "-pr" + str(pr_number)}" />
        </form>
        ''' for [app, pr_number] in pr_apps)}
        <form action="/delete_unused_services" method="post">
            <input type="submit" value="Delete unused services" />
       </form>
    """
    )


@app.route("/deploy_prod_app")
def deploy_prod_app():
    if not is_staff("cs61a"):
        return login()
    email = get_user()["email"]
    if not is_admin(course="cs61a", email=email):
        abort(401)
    app = request.args["app"]
    deploy_prod_app_sync(target_app=app, noreply=True)
    return html(f"Deploying <code>{app}</code> from master!")


@deploy_prod_app_sync.bind(app)
@validates_master_secret
def handle_deploy_prod_app_sync(app, is_staging, target_app):
    if app != "buildserver" or is_staging:
        abort(401)
    g = Github(get_secret(secret_name="GITHUB_ACCESS_TOKEN"))
    repo = g.get_repo(GITHUB_REPO)
    land_commit(
        repo.get_branch(repo.default_branch).commit.sha,
        repo,
        repo,
        None,
        [f"{target_app}/main.py"],
    )


@app.route("/trigger_build")
def trigger_build():
    if not is_staff("cs61a"):
        return login()
    email = get_user()["email"]
    if not is_admin(course="cs61a", email=email):
        abort(401)
    if "app" in request.args:
        target = request.args["app"]
    else:
        target = None

    pr_number = int(request.args["pr_number"])

    g = Github(get_secret(secret_name="GITHUB_ACCESS_TOKEN"))
    repo = g.get_repo(GITHUB_REPO)
    pr = repo.get_pull(pr_number)

    if DO_NOT_BUILD in [l.name for l in pr.labels]:
        return html(
            f"PR <code>{pr_number}</code> has a DO NOT BUILD label on it, so it cannot be built. Remove this label to build the PR."
        )

    trigger_build_sync(pr_number=pr_number, target_app=target, noreply=True)
    return html(f"Building PR <code>{pr_number}</code>!")


@trigger_build_sync.bind(app)
@validates_master_secret
def handle_trigger_build_sync(app, is_staging, pr_number, target_app=None):
    if app not in ("slack", "buildserver") or is_staging:
        raise PermissionError

    g = Github(get_secret(secret_name="GITHUB_ACCESS_TOKEN"))
    repo = g.get_repo(GITHUB_REPO)
    pr = repo.get_pull(pr_number)

    if DO_NOT_BUILD in [l.name for l in pr.labels]:
        raise PermissionError

    land_commit(pr.head.sha, repo, repo, pr, pr.get_files(), target_app=target_app)


@clear_queue.bind(app)
@only("buildserver", allow_staging=True)
def clear_queue():
    dequeue_and_build(get_github().get_repo(GITHUB_REPO))


@app.route("/delete_unused_services", methods=["POST"])
def delete_unused_services_handler():
    if not is_staff("cs61a"):
        return login()
    email = get_user()["email"]
    if not is_admin(course="cs61a", email=email):
        return login()
    delete_unused_services()
    return redirect(url_for("index"))


@app.route("/webhook", methods=["POST"])
def webhook():
    if not hmac.compare_digest(
        "sha1="
        + hmac.new(
            get_secret(secret_name="GITHUB_WEBHOOK_SECRET").encode("ascii"),
            request.get_data(),
            "sha1",
        ).hexdigest(),
        request.headers["X-Hub-Signature"],
    ):
        abort(401)

    payload = request.json

    g = Github(get_secret(secret_name="GITHUB_ACCESS_TOKEN"))

    if "pusher" in payload and payload["ref"] == "refs/heads/master":
        base_repo = g.get_repo(GITHUB_REPO)
        repo = g.get_repo(payload["repository"]["id"])
        sha = payload["after"]
        land_commit(
            sha,
            repo,
            base_repo,
            None,
            [
                file
                for commit in payload["commits"]
                for file in commit["added"] + commit["modified"] + commit["removed"]
            ],
        )
        delete_unused_services()

    if "pull_request" in payload:
        repo_id = payload["repository"]["id"]
        repo = g.get_repo(repo_id)
        pr = repo.get_pull(payload["pull_request"]["number"])

        if payload["action"] in ("opened", "synchronize", "reopened"):
            if repo.full_name != GITHUB_REPO:
                land_commit(pr.head.sha, repo, g.get_repo(GITHUB_REPO), pr, [])
            else:
                for target in determine_targets(repo, pr.get_files()):
                    report_build_status(
                        target,
                        pr.number,
                        pack(repo.clone_url, pr.head.sha),
                        BuildStatus.pushed,
                        None,
                        None,
                        private=True,
                    )

        elif payload["action"] == "closed":
            set_pr_comment("PR closed, shutting down PR builds...", pr)
            delete_unused_services(pr.number)
            set_pr_comment("All PR builds shut down.", pr)

    return ""


@get_base_hostname.bind(app)
@only("domains", allow_staging=True)
def get_base_hostname(target_app):
    return api.get_base_hostname(target_app)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True, threaded=False)

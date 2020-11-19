import hmac

from flask import Flask, abort, redirect, request
from github import Github

import api
from common.db import connect_db
from common.oauth_client import create_oauth_client, get_user, is_staff
from common.rpc.auth import is_admin
from common.rpc.buildserver import (
    deploy_prod_app_sync,
    get_base_hostname,
    trigger_build_sync,
)
from common.rpc.secrets import get_secret, only, validates_master_secret
from common.url_for import url_for
from deploy import delete_unused_services
from github_utils import set_pr_comment
from worker import land_commit

GITHUB_REPO = "Cal-CS-61A-Staff/cs61a-apps"

app = Flask(__name__)
if __name__ == "__main__":
    app.debug = True

create_oauth_client(app, "61a-buildserver")

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


@app.route("/")
def index():
    if not is_staff("cs61a"):
        return redirect(url_for("login"))
    email = get_user()["email"]
    if not is_admin(course="cs61a", email=email):
        abort(401)
    with connect_db() as db:
        apps = db("SELECT app FROM services WHERE pr_number=0", []).fetchall()
        pr_apps = db("SELECT app, pr_number FROM services WHERE pr_number>0 ORDER BY pr_number DESC", []).fetchall()
    return f"""
        <h1>61A Buildserver</h1>
        This service manages the deployment of the 61A website and various apps.
        {"".join(f'''
        <form action="/deploy_prod_app">
            <input type="submit" name="app" value="{app}" />
        </form>
        ''' for [app] in apps)}
        {"".join(f'''
        <form action="/trigger_build">
            <input type="submit" name="app" value="{app}" />
            <input type="submit" name="pr_number" value="{pr_number}" />
        </form>
        ''' for [app, pr_number] in pr_apps)}
        <form action="/delete_unused_services" method="post">
            <input type="submit" value="Delete unused services" />
       </form>
"""


@app.route("/deploy_prod_app")
def deploy_prod_app():
    if not is_staff("cs61a"):
        return redirect(url_for("login"))
    email = get_user()["email"]
    if not is_admin(course="cs61a", email=email):
        abort(401)
    deploy_prod_app_sync(target_app=request.args["app"], noreply=True)
    return ""


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
        return redirect(url_for("login"))
    email = get_user()["email"]
    if not is_admin(course="cs61a", email=email):
        abort(401)
    if "app" in request.args:
        target = request.args["app"]
    else:
        target = None
    trigger_build_sync(pr_number=int(request.args["pr_number"]), target_app=target, noreply=True)
    return ""


@trigger_build_sync.bind(app)
@validates_master_secret
def handle_trigger_build_sync(app, is_staging, pr_number, target_app="all"):
    if app not in ("slack", "buildserver") or is_staging:
        abort(401)

    g = Github(get_secret(secret_name="GITHUB_ACCESS_TOKEN"))
    repo = g.get_repo(GITHUB_REPO)
    pr = repo.get_pull(pr_number)
    land_commit(pr.head.sha, repo, repo, pr, pr.get_files(), target_app)


@app.route("/delete_unused_services", methods=["POST"])
def delete_unused_services_handler():
    if not is_staff("cs61a"):
        return redirect(url_for("login"))
    email = get_user()["email"]
    if not is_admin(course="cs61a", email=email):
        return redirect(url_for("login"))
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
                set_pr_comment(
                    f"PR updated. To trigger a build, click [here]({url_for('trigger_build', pr_number=pr.number)}).",
                    pr,
                )
                repo.get_commit(pr.head.sha).create_status(
                    "pending",
                    "https://buildserver.cs61a.org",
                    "You must rebuild the modified apps before merging",
                    "Pusher",
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

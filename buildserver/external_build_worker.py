# this is used to trigger the worker via Cloud Build
import sys

from github import Github

from app_config import App
from build import clone_commit
from common.rpc.secrets import get_secret
from conf import GITHUB_REPO
from worker import land_app_worker

if __name__ == "__main__":
    g = Github(get_secret(secret_name="GITHUB_ACCESS_TOKEN"))
    _, app_name, pr_number, sha, repo_id = sys.argv
    base_repo = g.get_repo(GITHUB_REPO)
    clone_commit(
        base_repo.clone_url,
        sha
        if repo_id == base_repo.full_name
        else base_repo.get_branch(base_repo.default_branch).commit.sha,
    )
    land_app_worker(App(app_name), int(pr_number), sha, g.get_repo(repo_id))

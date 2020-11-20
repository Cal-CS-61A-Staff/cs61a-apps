import os
import shutil
import sys

from github import Github
from github.Repository import Repository

from app_config import App
from build import clone_commit
from common.rpc.secrets import get_secret
from common.secrets import get_master_secret
from common.shell_utils import sh
from deploy import gen_service_name
import worker
import main


def run_highcpu_build(
    app: App,
    pr_number: int,
    sha: str,
    repo: Repository,
):
    for f in os.listdir("./deploy_files"):
        if f == "cloudbuild.yaml":
            # don't use this one, we don't want any caching
            continue
        shutil.copyfile(f"./deploy_files/{f}", f"./{f}")
    shutil.copyfile("./dockerfiles/buildserver.Dockerfile", "./Dockerfile")
    with open("Dockerfile", "a+") as f:
        f.seek(0)
        contents = f.read()
        contents = contents.replace("$APP_NAME", app.name)
        contents = contents.replace("$PR_NUMBER", str(pr_number))
        contents = contents.replace("$SHA", sha)
        contents = contents.replace("$REPO_ID", repo.full_name)
        contents = contents.replace("$MASTER_SECRET", get_master_secret())
        f.seek(0)
        f.truncate()
        f.write(contents)
    sh(
        "gcloud",
        "builds",
        "submit",
        "-q",
        "--tag",
        "gcr.io/cs61a-140900/temp-{}".format(gen_service_name(app.name, pr_number)),
        # "--machine-type=N1_HIGHCPU_32",
    )


# this is used to trigger the worker via Cloud Build
if __name__ == "__main__":
    g = Github(get_secret(secret_name="GITHUB_ACCESS_TOKEN"))
    _, app_name, pr_number, sha, repo_id = sys.argv
    base_repo = g.get_repo(main.GITHUB_REPO)
    clone_commit(
        base_repo.clone_url,
        sha
        if repo_id == base_repo.full_name
        else base_repo.get_branch(base_repo.default_branch).commit.sha,
    )
    worker.land_app_worker(App(app_name), int(pr_number), sha, g.get_repo(repo_id))

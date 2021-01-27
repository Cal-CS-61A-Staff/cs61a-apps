import os
import shutil

from github.Repository import Repository

from app_config import App
from common.secrets import get_master_secret
from common.shell_utils import sh
from deploy import gen_service_name


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
        contents = contents.replace("$BASE_IMAGE", app.config["build_image"])
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

import click

from common.shell_utils import sh
import os, shutil

ENV = "env"
REQ = "requirements.txt"


@click.command()
@click.argument("dir", default="./")
@click.argument("req", default="./")
@click.option("--reset", is_flag=True)
def venv(dir, req, reset):
    """Create a virtual environment in DIR.

    DIR is the location of the virtual env
    (minus the `env` folder itself). REQ is
    the location of the requirements file.
    Both of these arguments default to `./`.
    If you want to forcibly recreate an env,
    use the RESET option.
    """
    if not dir.endswith("/"):
        dir = dir + "/"
    if req.endswith("requirements.txt"):
        req = req[:-16]
    if not req.endswith("/"):
        req = req + "/"
    if os.path.exists(f"{dir}{ENV}"):
        if reset:
            shutil.rmtree(f"{dir}{ENV}")
        else:
            print("This environment already exists!")
            return
    sh("python3", "-m", "venv", f"{dir}{ENV}")
    sh(f"{dir}{ENV}/bin/pip3", "install", "-r", f"{req}{REQ}")

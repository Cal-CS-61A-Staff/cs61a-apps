import re
from typing import Optional, Tuple

from packaging.version import Version

import requests

from app_config import App

VERSION_REGEX = r"version=\"(\d*).(\d)*.\*\""


def get_latest_version(
    app: App, pr_number: int
) -> Tuple[Optional[Version], Optional[Version]]:
    """
    Finds the latest deployed version of the package, or `None` if no
    such version can be found. If we are making a prod build, it just finds
    the latest deployed prod version. If we are making a PR build, it returns
    both the latest deployed prod version, as well as the latest pre-release for
    that PR.
    """
    package_name = app.config["package_name"]
    data = requests.get(f"https://pypi.org/pypi/{package_name}/json")
    if data.status_code == 404:
        return None, None
    versions = [Version(release) for release in data.json()["releases"]]
    prod_versions = [version for version in versions if version.pre is None]
    pr_versions = [
        version
        for version in versions
        if version.pre is not None and version.pre[1] == pr_number
    ]
    latest_prod = max(prod_versions) if prod_versions else None
    latest_pr = max(pr_versions) if pr_versions else None

    return latest_prod, latest_pr


def update_setup_py(app: App, pr_number: int):
    with open("setup.py", "a+") as f:
        f.seek(0)
        setup_contents = f.read()
        match = re.search(VERSION_REGEX, setup_contents)
        if match is None:
            raise Exception("Could not find version in setup.py")
        major, minor = int(match.group(1)), int(match.group(2))
        latest_prod_version, latest_pr_version = get_latest_version(app, pr_number)
        if latest_prod_version is None:
            micro = 0
        else:
            if (
                latest_prod_version.major > major
                or latest_prod_version.major == major
                and latest_prod_version.minor > minor
            ):
                raise Exception(
                    f"Latest version {latest_prod_version} is greater than current build {major}.{minor}"
                )
            if (
                latest_prod_version.major == major
                and latest_prod_version.minor == minor
            ):
                micro = latest_prod_version.micro + 1
            else:
                micro = 0

        if latest_pr_version is None:
            dev_number = 0
        else:
            dev_number = latest_pr_version.dev + 1

        if pr_number == 0:
            next_version = Version(f"{major}.{minor}.{micro}")
        else:
            next_version = Version(
                f"{major}.{minor}.{micro}b{pr_number}.dev{dev_number}"
            )

        f.seek(0)
        f.truncate()
        f.write(re.sub(VERSION_REGEX, f'version="{next_version}"', setup_contents))

        app.deployed_pypi_version = str(next_version)

from dataclasses import dataclass
from typing import List, Literal, Optional, TypedDict

import yaml

from common.shell_utils import tmp_directory

WEB_DEPLOY_TYPES = {"flask", "docker", "static"}
CLOUD_RUN_DEPLOY_TYPES = {"flask", "docker"}


class Config(TypedDict):
    build_type: Literal[
        "create_react_app", "oh_queue", "webpack", "61a_website", "none"
    ]
    deploy_type: Literal[
        "flask", "flask-pandas", "docker", "pypi", "cloud_function", "static", "none"
    ]
    highcpu_build: bool
    cpus: int
    memory_limit: str
    first_party_domains: List[str]
    concurrency: int
    tasks: List["Task"]
    dependencies: List["Dependency"]
    repo: Optional[str]
    package_name: str
    static_consumers: List[str]


class Task(TypedDict):
    name: str
    schedule: str


class Dependency(TypedDict):
    repo: str
    src: str
    dest: str


@dataclass
class App:
    name: str
    config: Config

    # updated by deploy.py, since PyPI takes a while to update
    deployed_pypi_version: Optional[str]

    def __init__(self, name: str):
        self.name = name
        self.deployed_pypi_version = None
        with tmp_directory():
            with open(f"{name}/deploy.yaml") as f:
                self.config = Config(**yaml.safe_load(f))
                self.config["highcpu_build"] = self.config.get("highcpu_build", False)
                self.config["cpus"] = self.config.get("cpus", 1)
                self.config["memory_limit"] = self.config.get("memory_limit", "256M")
                self.config["first_party_domains"] = self.config.get(
                    "first_party_domains", [f"{name}.cs61a.org"]
                )
                self.config["concurrency"] = self.config.get("concurrency", 80)
                self.config["tasks"] = self.config.get("tasks", [])
                self.config["dependencies"] = self.config.get("dependencies", [])
                self.config["package_name"] = self.config.get("package_name", name)
                self.config["static_consumers"] = self.config.get(
                    "static_consumers", []
                )
                self.config["repo"] = self.config.get("repo")

    def __str__(self):
        return self.name

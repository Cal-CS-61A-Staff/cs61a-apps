from dataclasses import dataclass
from typing import List, Literal, Optional, TypedDict

import yaml

from common.shell_utils import tmp_directory

CLOUD_RUN_DEPLOY_TYPES = {"flask", "flask-pandas", "docker"}
NO_PR_BUILD_DEPLOY_TYPES = {"service", "cloud_function", "none"}
WEB_DEPLOY_TYPES = {
    "flask",
    "flask-pandas",
    "docker",
    "hosted",
    "static",
    "cloud_function",
}


Permission = Literal[
    "rpc",
    "database",
    "storage",
    "logging",
    "iam_admin",
    "cloud_run_admin",
    "cloud_functions_admin",
]


class Config(TypedDict):
    target: str
    match: List[str]
    build_type: Optional[
        Literal[
            "create_react_app",
            "oh_queue",
            "webpack",
            "61a_website",
            "hugo",
            "jekyll",
            "none",
        ]
    ]
    deploy_type: Literal[
        "flask",
        "flask-pandas",
        "docker",
        "pypi",
        "cloud_function",
        "static",
        "service",
        "hosted",
        "none",
    ]
    build_image: Optional[str]
    cpus: int
    memory_limit: str
    first_party_domains: List[str]
    concurrency: int
    tasks: List["Task"]
    dependencies: List["Dependency"]
    repo: Optional[str]
    package_name: str
    static_consumers: List[str]
    service: "Service"
    pr_consumers: List[str]
    permissions: List[Permission]


class Task(TypedDict):
    name: str
    schedule: str


class Dependency(TypedDict):
    repo: str
    src: str
    dest: str


class Service(TypedDict):
    host: str
    root: str
    zone: str
    name: str


@dataclass
class App:
    name: str
    config: Optional[Config]

    # updated by deploy.py, since PyPI takes a while to update
    deployed_pypi_version: Optional[str]

    def __init__(self, name: str, data: Optional[dict]):
        if data is None:
            self.config = None
            return

        self.config = Config(**data)
        self.config["build_type"] = self.config.get("build_type", None)
        self.config["build_image"] = self.config.get("build_image", None)
        self.config["cpus"] = self.config.get("cpus", 1)
        self.config["memory_limit"] = self.config.get("memory_limit", "256M")
        self.config["first_party_domains"] = self.config.get(
            "first_party_domains", [f"{name}.cs61a.org"]
        )
        self.config["concurrency"] = self.config.get("concurrency", 80)
        self.config["tasks"] = self.config.get("tasks", [])
        self.config["dependencies"] = self.config.get("dependencies", [])
        self.config["package_name"] = self.config.get("package_name", name)
        self.config["static_consumers"] = self.config.get("static_consumers", [])
        self.config["repo"] = self.config.get("repo")
        self.config["service"] = self.config.get("service")
        self.config["pr_consumers"] = self.config.get("pr_consumers", [name])
        self.config["permissions"] = self.config.get("permissions", ["rpc", "database"])

    def __str__(self):
        return self.name

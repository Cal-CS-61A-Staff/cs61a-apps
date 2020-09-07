from dataclasses import dataclass
from typing import List, Literal, Optional, TypedDict

import yaml

from shell_utils import tmp_directory

WEB_DEPLOY_TYPES = {"flask", "docker"}


class Config(TypedDict):
    build_type: Literal["create_react_app", "oh_queue", "none"]
    deploy_type: Literal["flask", "docker", "none"]
    memory_limit: str
    first_party_domains: List[str]
    concurrency: int
    tasks: List["Task"]


class Task(TypedDict):
    name: str
    schedule: str


@dataclass
class App:
    name: str
    config: Config

    def __init__(self, name: str):
        self.name = name
        with tmp_directory():
            with open(f"{name}/deploy.yaml") as f:
                self.config = Config(**yaml.safe_load(f))
                self.config["memory_limit"] = self.config.get("memory_limit", "256M")
                self.config["first_party_domains"] = self.config.get(
                    "first_party_domains", [f"{name}.cs61a.org"]
                )
                self.config["concurrency"] = self.config.get("concurrency", 80)
                self.config["tasks"] = self.config.get("tasks", [])

    def __str__(self):
        return self.name

from __future__ import annotations

import os
from abc import ABC
from pathlib import Path
from typing import Sequence

from fs_utils import normalize_path
from utils import HashState


class Context(ABC):
    def __init__(self, repo_root: str, cwd: str):
        self.repo_root = repo_root
        self.cwd = os.path.abspath(cwd)

    def absolute(self, path: str):
        return normalize_path(self.repo_root, self.cwd, path)

    def relative(self, path: str):
        return str(
            os.path.relpath(
                Path(self.repo_root).joinpath(self.absolute(path)), self.cwd
            )
        )

    def sh(self, cmd: str):
        raise NotImplementedError

    def add_dep(self, dep: str):
        self.add_deps([dep])

    def add_deps(self, deps: Sequence[str]):
        raise NotImplementedError

    def input(self, *, file: str, sh: str):
        raise NotImplementedError


class MemorizeContext(Context):
    def __init__(self, repo_root: str, cwd: str, hashstate: HashState):
        super().__init__(repo_root, cwd)
        self.hashstate = hashstate
        self.inputs = []

    def sh(self, cmd: str):
        self.hashstate.record("sh", cmd)

    def add_deps(self, deps: Sequence[str]):
        self.hashstate.record("add_deps", deps)
        for dep in deps:
            self.inputs.append(self.absolute(dep))

    def input(self, *, file: str, sh: str):
        self.hashstate.record("input", file, sh)
        if file is not None:
            self.inputs.append(self.absolute(file))

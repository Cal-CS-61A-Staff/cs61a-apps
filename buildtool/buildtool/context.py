from __future__ import annotations

import os
from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union

from fs_utils import normalize_path
from common.hash_utils import HashState

Env = Dict[str, Union[str, List[str]]]


@dataclass
class ContextualRelativePath:
    path: str
    context: Context

    def resolve(self):
        return str(self)

    def __str__(self):
        return os.path.relpath(
            Path(self.context.repo_root).joinpath(self.path), self.context.cwd
        )


class DotDict:
    def __init__(self):
        self.items = {}

    def __getitem__(self, item):
        return self.items[item]

    def __setitem__(self, key, value):
        self.items[key] = value


class Context(ABC):
    def __init__(self, repo_root: str, cwd: str):
        self.repo_root = repo_root
        self.cwd = os.path.abspath(cwd)
        self.deps = DotDict()

    def absolute(self, path: str):
        return normalize_path(self.repo_root, self.cwd, path)

    def relative(self, path: str):
        return ContextualRelativePath(self.absolute(path), self)

    def chdir(self, dest: str):
        self.cwd = os.path.abspath(
            Path(self.repo_root).joinpath(
                normalize_path(self.repo_root, self.cwd, dest)
            )
        )

    def sh(self, cmd: str, env: Env = None):
        raise NotImplementedError

    def add_dep(self, dep: str):
        self.add_deps([dep])

    def add_deps(self, deps: Sequence[str]):
        raise NotImplementedError

    def input(self, *, file: Optional[str], sh: Optional[str], env: Env = None):
        raise NotImplementedError


class MemorizeContext(Context):
    def __init__(self, repo_root: str, cwd: str, hashstate: HashState):
        super().__init__(repo_root, cwd)
        self.hashstate = hashstate
        self.inputs = []
        self.uses_dynamic_inputs = False
        self.hashstate.record(self.absolute(self.cwd))

    def chdir(self, dest: str):
        super().chdir(dest)
        self.hashstate.record("chdir", dest)

    def sh(self, cmd: str, env: Env = None):
        self.hashstate.record("sh", cmd, env)

    def add_deps(self, deps: Sequence[str]):
        self.hashstate.record("add_deps", deps)
        for dep in deps:
            if dep.startswith(":"):
                self.inputs.append(dep)
            else:
                self.inputs.append(self.absolute(dep))

    def input(self, *, file: Optional[str], sh: Optional[str], env: Env = None):
        self.uses_dynamic_inputs = True
        self.hashstate.record("input", file, sh, env)
        if file is not None:
            self.inputs.append(self.absolute(file))

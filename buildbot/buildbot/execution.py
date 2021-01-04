from __future__ import annotations

import hashlib
from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from queue import Queue
from shutil import rmtree
from threading import Thread
from typing import Callable, List, Optional, Sequence, Set

from fs_utils import copy_helper, find_root, normalize_path
from loader import Rule
from utils import BuildException, HashState

from common.shell_utils import sh as run_shell


class Context(ABC):
    def __init__(self, repo_root: str, cwd: str):
        self.repo_root = repo_root
        self.cwd = cwd

    def resolve(self, path: str):
        return normalize_path(self.repo_root, self.cwd, path)

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

    def sh(self, cmd: str):
        self.hashstate.record("sh", cmd)

    def add_deps(self, deps: Sequence[str]):
        self.hashstate.record("add_deps", deps)

    def input(self, *, file: str, sh: str):
        self.hashstate.record("input", file, sh)


class PreviewContext(MemorizeContext):
    def __init__(
        self,
        repo_root: str,
        cwd: str,
        hashstate: HashState,
        dep_fetcher: Callable[[str], str],
        cache_fetcher: Callable[[str, str], str],
    ):
        super().__init__(repo_root, cwd, hashstate)

        self.inputs = []
        self.outputs = []
        self.dep_fetcher = dep_fetcher
        self.cache_fetcher = cache_fetcher

    def add_deps(self, deps: List[str]):
        super().add_deps(deps)
        for dep in deps:
            self.inputs.append(self.resolve(dep))

    def input(self, *, file: str = None, sh: str = None):
        super().input(file=file, sh=sh)
        if file is not None:
            path = self.resolve(file)
            self.inputs.append(path)
            return self.dep_fetcher(path)
        else:
            return self.cache_fetcher(
                self.hashstate.state(),
                hashlib.md5(sh.encode("utf-8")).hexdigest(),
            )


class ExecutionContext(MemorizeContext):
    def __init__(
        self,
        repo_root: str,
        cwd: str,
        hashstate: HashState,
        load_deps: Callable[[Sequence[str]], None],
        memorize: Callable[[str, str, str], None],
    ):
        super().__init__(repo_root, cwd, hashstate)
        self.load_deps = load_deps
        self.memorize = memorize

    def sh(self, cmd: str):
        super().sh(cmd)
        run_shell(cmd, shell=True, cwd=self.cwd)

    def add_deps(self, deps: Sequence[str]):
        super().add_deps(deps)
        self.load_deps([self.resolve(dep) for dep in deps])

    def input(self, *, file: str = None, sh: str = None):
        super().input(file=file, sh=sh)
        if file is not None:
            self.load_deps([self.resolve(file)])
            with open(self.resolve(file), "r") as f:
                return f.read()
        else:
            out = run_shell(sh, shell=True, cwd=self.cwd, capture_output=True).decode(
                "utf-8"
            )
            self.memorize(
                self.hashstate.state(), hashlib.md5(sh.encode("utf-8")).hexdigest(), out
            )
            return out

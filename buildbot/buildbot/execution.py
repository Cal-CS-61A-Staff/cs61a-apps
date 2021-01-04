from __future__ import annotations

import hashlib
import os
from abc import ABC
from pathlib import Path
from typing import Callable, Sequence

from fs_utils import normalize_path
from utils import HashState

from common.shell_utils import sh as run_shell


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

        self.dep_fetcher = dep_fetcher
        self.cache_fetcher = cache_fetcher

    def input(self, *, file: str = None, sh: str = None):
        super().input(file=file, sh=sh)
        if file is not None:
            return self.dep_fetcher(self.absolute(file))
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
        self.load_deps([self.absolute(dep) for dep in deps])

    def input(self, *, file: str = None, sh: str = None):
        super().input(file=file, sh=sh)
        if file is not None:
            self.load_deps([self.absolute(file)])
            with open(self.absolute(file), "r") as f:
                return f.read()
        else:
            out = run_shell(sh, shell=True, cwd=self.cwd, capture_output=True).decode(
                "utf-8"
            )
            self.memorize(
                self.hashstate.state(), hashlib.md5(sh.encode("utf-8")).hexdigest(), out
            )
            return out

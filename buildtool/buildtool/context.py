from __future__ import annotations

import os
from abc import ABC
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, TYPE_CHECKING, Union

from common.hash_utils import HashState
from fs_utils import normalize_path
from utils import BuildException

if TYPE_CHECKING:
    from state import Rule

Env = Dict[str, Union[str, List[str]]]


@dataclass
class ContextualRelativePath:
    path: str
    context: Context

    def resolve(self):
        return os.path.relpath(self.path, self.context.cwd)

    def __str__(self):
        return self.resolve()


class DotDict:
    def __init__(self):
        self.items = {}

    def __getitem__(self, item):
        return self.items[item]

    def __getattr__(self, item):
        return self.items[item]

    def __setitem__(self, key, value):
        self.items[key] = value


class Context(ABC):
    def __init__(self, cwd: str, macros: Dict[str, Callable]):
        self.cwd = cwd
        self.deps = DotDict()
        for name, macro in macros.items():
            if hasattr(self, name):
                raise BuildException(f"Macro {name} shadows existing Context attribute")
            setattr(
                self,
                name,
                lambda *args, __macro=macro, **kwargs: __macro(self, *args, **kwargs),
            )

    def absolute(self, path: str):
        return normalize_path(self.cwd, path)

    def relative(self, path: str):
        return ContextualRelativePath(self.absolute(path), self)

    def _resolve(self, dep: str):
        dep = str(dep)
        if dep.startswith(":"):
            return dep
        else:
            return self.absolute(dep)

    def chdir(self, dest: str):
        self.cwd = normalize_path(self.cwd, dest)

    def sh(self, cmd: str, env: Env = None):
        raise NotImplementedError

    def add_dep(self, dep: str, *, load_provided=False, defer=False):
        raise NotImplementedError

    def add_deps(self, deps: Sequence[str]):
        for dep in deps:
            self.add_dep(dep)

    def input(self, sh: Optional[str], *, env: Env = None):
        raise NotImplementedError


class MemorizeContext(Context):
    never_defer = False

    def __init__(
        self,
        cwd: str,
        macros: Dict[str, Callable],
        hashstate: HashState,
        dep_fetcher: Callable[[str], "Rule"],
    ):
        super().__init__(cwd, macros)
        self.hashstate = hashstate
        self.dep_fetcher = dep_fetcher
        self.inputs = []
        self.deferred_inputs = []
        self.uses_dynamic_inputs = False
        self.hashstate.record(self.absolute("."))

    def chdir(self, dest: str):
        super().chdir(dest)
        self.hashstate.record("chdir", dest)

    def sh(self, cmd: str, env: Env = None):
        self.hashstate.record("sh", cmd, env)

    def add_dep(self, dep: str, *, load_provided=False, defer=False):
        if load_provided and defer:
            raise BuildException("Cannot load provided value of a deferred dependency")

        dep = str(dep)

        if (
            dep.startswith(":")
            and not defer
            and not load_provided
            and not self.never_defer
        ):
            defer = True

        if defer and self.never_defer:
            raise BuildException("Setup rules cannot defer dependencies")

        if defer:
            self.deferred_inputs.append(dep)
        else:
            self.hashstate.record("add_dep", dep)
            self.inputs.append(self._resolve(dep))

        if load_provided:
            rule = self.dep_fetcher(self._resolve(dep))
            if rule is None:
                raise BuildException("Cannot load provided value of a source file")
            self.deps[dep] = rule.provided_value
            if rule.name:
                self.deps[rule.name] = rule.provided_value

        return defer

    def input(self, sh: Optional[str], *, env: Env = None):
        self.uses_dynamic_inputs = True
        self.hashstate.record("input", sh, env)

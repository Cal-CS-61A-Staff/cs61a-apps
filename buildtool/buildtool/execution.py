from __future__ import annotations

import hashlib
from pathlib import Path
from subprocess import CalledProcessError
from typing import Callable, Collection, Optional, Sequence

from colorama import Style

from cache import make_cache_memorize
from context import MemorizeContext
from fs_utils import copy_helper
from monitoring import log
from utils import BuildException, HashState, MissingDependency
from state import BuildState, Rule

from common.shell_utils import sh as run_shell


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
        run_shell(cmd, shell=True, cwd=self.cwd, quiet=True, capture_output=True)

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
            out = run_shell(
                sh, shell=True, cwd=self.cwd, capture_output=True, quiet=True
            ).decode("utf-8")
            self.memorize(
                self.hashstate.state(), hashlib.md5(sh.encode("utf-8")).hexdigest(), out
            )
            return out


def build(
    build_state: BuildState,
    rule: Rule,
    deps: Collection[str],
    *,
    scratch_path: Optional[Path],
):
    """
    All the dependencies that can be determined from caches have been
    obtained. Now we need to run. Either we will successfully finish everything,
    or we will get a missing dependency and have to requeue
    """
    memorize = make_cache_memorize(build_state.cache_directory)

    in_sandbox = scratch_path is not None

    loaded_deps = set()

    def load_deps(deps):
        deps = set(deps) - loaded_deps
        # check that these deps are built! Since they have not been checked by the PreviewExecution.
        missing_deps = []
        for dep in deps:
            if dep not in build_state.source_files:
                rule = build_state.target_rule_lookup.lookup(build_state, dep)
                if rule not in build_state.ready:
                    missing_deps.append(dep)
        if missing_deps:
            raise MissingDependency(*missing_deps)
        loaded_deps.update(deps)
        if in_sandbox:
            log(f"Loading dependencies {deps} into sandbox")
            copy_helper(
                src_root=build_state.repo_root,
                dest_root=scratch_path,
                src_names=deps,
                symlink=True,
            )

    load_deps(deps)
    hashstate = HashState()
    for dep in rule.deps:
        hashstate.update(dep.encode("utf-8"))
        with open(dep, "rb") as f:
            hashstate.update(f.read())

    ctx = ExecutionContext(
        scratch_path if in_sandbox else build_state.repo_root,
        scratch_path.joinpath(rule.location)
        if in_sandbox
        else Path(build_state.repo_root).joinpath(rule.location),
        hashstate,
        load_deps,
        memorize,
    )

    try:
        rule.impl(ctx)
    except CalledProcessError as e:
        raise BuildException(
            "".join(
                [
                    str(e) + "\n",
                    Style.RESET_ALL,
                    f"Location: {scratch_path}\n",
                    e.stdout.decode("utf-8"),
                    e.stderr.decode("utf-8")[:-1],
                ]
            )
        )

    if in_sandbox:
        try:
            copy_helper(
                src_root=scratch_path,
                src_names=rule.outputs,
                dest_root=build_state.repo_root,
            )
        except FileNotFoundError as e:
            raise BuildException(
                f"Output file {e.filename} from rule {rule} was not generated."
            )

    for input_path in ctx.inputs:
        hashstate.update(input_path.encode("utf-8"))
        with open(input_path, "rb") as f:
            hashstate.update(f.read())

    return hashstate.state()

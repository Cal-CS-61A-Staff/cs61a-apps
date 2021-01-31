from __future__ import annotations

import os
import traceback
from pathlib import Path
from subprocess import CalledProcessError
from typing import Callable, Collection, Optional, Sequence

from colorama import Style

from cache import make_cache_memorize
from common.shell_utils import sh as run_shell
from context import Env, MemorizeContext
from fs_utils import copy_helper, hash_file
from monitoring import log
from state import BuildState, Rule
from utils import BuildException, MissingDependency
from common.hash_utils import HashState


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
        self.sh_queue = []
        os.makedirs(self.cwd, exist_ok=True)

    def normalize_single(self, path: str):
        if path.startswith("@//"):
            return os.path.abspath(os.path.join(os.curdir, path[3:]))
        elif path.startswith("//"):
            return os.path.abspath(os.path.join(self.repo_root, path[2:]))
        else:
            return path

    def normalize(self, env: Optional[Env]):
        if env is None:
            return {}
        out = {}
        for key in env:
            if isinstance(env[key], str):
                out[key] = self.normalize_single(env[key])
            else:
                out[key] = ":".join(
                    self.normalize_single(component) for component in env[key]
                )
        return out

    def sh(self, cmd: str, env: Env = None):
        super().sh(cmd=cmd, env=env)
        self.sh_queue.append([cmd, self.cwd, self.normalize(env)])

    def run_shell_queue(self):
        for cmd, cwd, env in self.sh_queue:
            log("RUNNING cmd:", cmd)
            run_shell(
                cmd,
                shell=True,
                cwd=cwd,
                quiet=True,
                capture_output=True,
                inherit_env=False,
                env=env,
            )
        self.sh_queue = []

    def add_deps(self, deps: Sequence[str]):
        super().add_deps(deps)
        self.run_shell_queue()
        self.load_deps(
            [dep if dep.startswith(":") else self.absolute(dep) for dep in deps]
        )

    def input(
        self, *, file: Optional[str] = None, sh: Optional[str] = None, env: Env = None
    ):
        # we want the state *before* running the action
        state = self.hashstate.state()
        super().input(file=file, sh=sh, env=env)
        self.run_shell_queue()
        if file is not None:
            self.load_deps([self.absolute(file)])
            with open(self.absolute(file), "r") as f:
                return f.read()
        else:
            log("RUNNING", sh)
            out = run_shell(
                sh,
                shell=True,
                cwd=self.cwd,
                capture_output=True,
                quiet=True,
                inherit_env=False,
                env=self.normalize(env),
            ).decode("utf-8")
            self.memorize(state, HashState().record(sh, env).state(), out)
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
    cache_memorize, _ = make_cache_memorize(build_state.cache_directory)

    in_sandbox = scratch_path is not None

    loaded_deps = set()

    def load_deps(deps):
        deps = set(deps) - loaded_deps
        # check that these deps are built! Since they have not been checked by the PreviewExecution.
        missing_deps = []
        for dep in deps:
            if dep not in build_state.source_files:
                dep_rule = build_state.target_rule_lookup.lookup(build_state, dep)
                if dep_rule not in build_state.ready:
                    missing_deps.append(dep)
        if missing_deps:
            raise MissingDependency(*missing_deps)
        loaded_deps.update(deps)
        if in_sandbox:
            log(f"Loading dependencies {deps} into sandbox")
            copy_helper(
                src_root=build_state.repo_root,
                dest_root=scratch_path,
                src_names=[dep for dep in deps if not dep.startswith(":")],
                symlink=not rule.do_not_symlink,
            )

    load_deps(deps)
    hashstate = HashState()

    ctx = ExecutionContext(
        scratch_path if in_sandbox else build_state.repo_root,
        scratch_path.joinpath(rule.location)
        if in_sandbox
        else Path(build_state.repo_root).joinpath(rule.location),
        hashstate,
        load_deps,
        cache_memorize,
    )

    for dep in rule.deps:
        dep_rule = build_state.target_rule_lookup.try_lookup(dep)
        if dep.startswith(":"):
            setattr(ctx.deps, dep[1:], dep_rule.provided_value)
        else:
            hashstate.update(dep.encode("utf-8"))
            hashstate.update(hash_file(dep))
        if dep not in build_state.source_files:
            ctx.deps[dep] = dep_rule.provided_value

    try:
        rule.provided_value = rule.impl(ctx)
        for out in rule.outputs:
            # needed so that if we ask for another output, we don't panic if it's not in the cache
            hashstate.record(out)
        if in_sandbox:
            ctx.run_shell_queue()
    except CalledProcessError as e:
        raise BuildException(
            "".join(
                [
                    str(e) + "\n",
                    Style.RESET_ALL,
                    f"Location: {scratch_path}\n",
                    f"Working Directory: {ctx.cwd}\n",
                    e.stdout.decode("utf-8"),
                    e.stderr.decode("utf-8"),
                    traceback.format_exc(),
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
        if input_path.startswith(":"):
            # don't hash rule deps
            continue
        hashstate.update(input_path.encode("utf-8"))
        hashstate.update(hash_file(input_path))

    return hashstate.state()

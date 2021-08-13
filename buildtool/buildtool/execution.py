from __future__ import annotations

import os
import traceback
from pathlib import Path
from subprocess import CalledProcessError
from typing import Callable, Collection, Dict, List, Optional, Sequence

from colorama import Style

from cache import make_cache_store
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
        base: str,
        cwd: str,
        macros: Dict[str, Callable],
        hashstate: HashState,
        dep_fetcher: Callable[[str], Rule],
        memorize: Callable[[str, str, str], None],
    ):
        super().__init__(cwd, macros, hashstate, dep_fetcher)
        self.base = base
        self.memorize = memorize
        self.sh_queue = []
        self.out_of_date_deps = []
        os.makedirs(os.path.join(self.base, self.cwd), exist_ok=True)

    def normalize_single(self, path: str):
        if path.startswith("@//"):
            return os.path.abspath(os.path.join(os.curdir, path[3:]))
        elif path.startswith("//"):
            return os.path.abspath(os.path.join(self.base, path[2:]))
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
                cwd=os.path.join(self.base, cwd),
                quiet=True,
                capture_output=True,
                inherit_env=False,
                env=env,
            )
        self.sh_queue = []

    def add_dep(self, dep: str, *, load_provided=False, defer=False):
        defer = super().add_dep(dep, load_provided=load_provided, defer=defer)
        if not defer:
            dep = self._resolve(dep)
            try:
                self.dep_fetcher(dep)
            except MissingDependency:
                self.out_of_date_deps.append(dep)

    def input(self, sh: Optional[str] = None, *, env: Env = None):
        # we want the state *before* running the action
        state = self.hashstate.state()
        super().input(sh, env=env)
        if self.out_of_date_deps:
            raise MissingDependency(*self.out_of_date_deps)
        self.run_shell_queue()
        log("RUNNING", sh)
        out = run_shell(
            sh,
            shell=True,
            cwd=os.path.join(self.base, self.cwd),
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
    *,
    precomputed_deps: Optional[List[str]] = None,
    scratch_path: Optional[Path],
    skip_cache_key: bool,
):
    """
    All the dependencies that can be determined from caches have been
    obtained. Now we need to run. Either we will successfully finish everything,
    or we will get a missing dependency and have to requeue
    """
    cache_store_string, _ = make_cache_store(build_state.cache_directory)

    in_sandbox = scratch_path is not None

    loaded_deps = set()

    def dep_fetcher(dep, *, initial_load=False):
        if dep not in loaded_deps and in_sandbox:
            if not initial_load:
                raise BuildException(
                    f"New dep {dep} found when rerunning rule, it's likely not deterministic!"
                )
            if not dep.startswith(":"):
                log(f"Loading dependency {dep} into sandbox")
                copy_helper(
                    src_root=os.curdir,
                    dest_root=scratch_path,
                    src_names=[dep],
                    symlink=not rule.do_not_symlink,
                )

        # check that these deps are built! Since they may not have been checked by the PreviewExecution.
        dep_rule = None
        if dep not in build_state.source_files:
            dep_rule = build_state.target_rule_lookup.lookup(build_state, dep)
            if dep_rule not in build_state.ready:
                raise MissingDependency(dep)

        loaded_deps.add(dep)

        return dep_rule

    if precomputed_deps:
        assert in_sandbox
        for dep in precomputed_deps:
            dep_fetcher(dep, initial_load=True)

    hashstate = HashState()

    ctx = ExecutionContext(
        scratch_path if in_sandbox else os.curdir,
        rule.location,
        build_state.macros,
        hashstate,
        dep_fetcher,
        cache_store_string,
    )

    try:
        if not skip_cache_key:
            for out in rule.outputs:
                # needed so that if we ask for another output, we don't panic if it's not in the cache
                hashstate.record(out)
        provided_value = rule.impl(ctx)
        if ctx.out_of_date_deps:
            raise MissingDependency(*ctx.out_of_date_deps)
        if in_sandbox:
            ctx.run_shell_queue()
    except CalledProcessError as e:
        raise BuildException(
            "".join(
                [
                    str(e) + "\n",
                    Style.RESET_ALL,
                    f"Location: {scratch_path}\n",
                    f"Working Directory: {scratch_path}/{ctx.cwd}\n",
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
                dest_root=os.curdir,
            )
        except FileNotFoundError as e:
            raise BuildException(
                f"Output file {e.filename} from rule {rule} was not generated."
            )

    if not skip_cache_key:
        for input_path in ctx.inputs:
            if input_path.startswith(":"):
                # don't hash rule deps
                continue
            hashstate.update(input_path.encode("utf-8"))
            hashstate.update(hash_file(input_path))
    hashstate.record("done")

    return provided_value, hashstate.state() if not skip_cache_key else None

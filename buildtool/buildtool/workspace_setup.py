import os
from typing import Dict, List, Optional, Sequence, Set

from cache import make_cache_fetcher, make_cache_memorize
from context import Env
from execution import ExecutionContext
from fs_utils import hash_file
from monitoring import create_status_monitor, log
from state import Rule, TargetLookup
from utils import BuildException, CacheMiss
from common.hash_utils import HashState


class WorkspaceExecutionContext(ExecutionContext):
    def __init__(
        self,
        hashstate: HashState,
    ):
        super().__init__(
            os.curdir, os.curdir, hashstate, lambda *args: None, lambda *args: None
        )

    def add_deps(self, deps: Sequence[str]):
        raise BuildException("Cannot add dependencies dynamically in a setup rule.")

    def input(
        self,
        *,
        file: Optional[str] = None,
        sh: Optional[str] = None,
        env: Optional[Env] = None,
    ):
        if file is not None:
            raise BuildException(
                f"Cannot add dependencies dynamically in a setup rule. Add {file} as a static dependency "
                f'then use input(sh="cat {file}") instead.'
            )
        else:
            return super().input(file=file, sh=sh, env=env)

    def normalize(self, env: Optional[Env]):
        if env is None:
            env = {}
        return super().normalize({**env, **os.environ})


def initialize_workspace(
    setup_rule_lookup: TargetLookup,
    setup_targets: List[str],
    state_directory: str,
    quiet: bool,
):
    # we don't need the indirect lookup as we only have rule and source deps
    direct_lookup: Dict[str, Rule] = setup_rule_lookup.direct_lookup
    work_queue = []
    for setup_target in setup_targets:
        if setup_target not in direct_lookup:
            raise BuildException(f"Unknown or unspecified setup target {setup_target}")
        work_queue.append(direct_lookup[setup_target])

    rebuilt: Set[str] = set()
    ready: Set[str] = set()

    cache_fetcher, _ = make_cache_fetcher(state_directory)
    cache_memorize, _ = make_cache_memorize(state_directory)

    if work_queue:
        status_monitor = create_status_monitor(1, quiet)
        status_monitor.move(total=len(work_queue))

    while work_queue:
        todo = work_queue.pop()
        log(f"Popping setup rule {todo} off work queue")
        hashstate = HashState()
        ctx = WorkspaceExecutionContext(hashstate)
        unchecked_rules = []
        for dep in todo.deps:
            hashstate.record(dep)
            if dep.startswith(":"):
                if dep not in direct_lookup:
                    raise BuildException(f"Unable to find setup rule {dep}")
                dep_rule = direct_lookup[dep]
                if dep_rule not in ready:
                    unchecked_rules.append(dep_rule)
                    continue
                ctx.deps[dep] = dep_rule.provided_value
                setattr(ctx.deps, dep[1:], dep_rule.provided_value)
            else:
                try:
                    hashstate.update(hash_file(dep))
                except FileNotFoundError:
                    raise BuildException(f"Source file {dep} not found.")

        if unchecked_rules:
            for dep in unchecked_rules:
                if dep not in work_queue:
                    log(f"Setup rule {todo} is enqueuing {dep}")
                    status_monitor.move(total=1)
                    work_queue.append(dep)
                else:
                    log(
                        f"Setup rule {todo} is waiting on {dep}, which is already enqueued"
                    )
                dep.runtime_dependents.add(todo)
                todo.pending_rule_dependencies.add(dep)
        else:
            # our dependent rules are ready, now we need to see if we need to rerun
            todo.provided_value = todo.impl(ctx)

            if todo.name is None:
                raise BuildException(
                    f"All setup rules must have names, but {todo} does not."
                )

            try:
                ok = cache_fetcher("workspace", todo.name) == hashstate.state()
                if not ok:
                    log(f"State mismatch for rule {todo}, need to rerun")
            except CacheMiss:
                log(f"State not found for rule {todo}, need to run for first time")
                ok = False

            for dep in todo.deps:
                if dep.startswith(":"):
                    if direct_lookup[dep] in rebuilt:
                        log(
                            f"Dependency {dep} of setup rule {todo} was rebuilt, so we must rebuild {todo} as well"
                        )
                        ok = False

            for out in todo.outputs:
                if not os.path.exists(out):
                    log(f"Output {out} is missing for setup rule {todo}, forcing rerun")
                    ok = False
                    break

            if not ok:
                # we need to fully run
                ctx.run_shell_queue()
                rebuilt.add(todo)
                cache_memorize("workspace", todo.name, hashstate.state())

            # either way, now we can trigger our dependents
            ready.add(todo)
            for dep in todo.runtime_dependents:
                dep.pending_rule_dependencies.remove(todo)
                if not dep.pending_rule_dependencies:
                    work_queue.append(dep)
                    status_monitor.move(total=1)

        status_monitor.move(curr=1)

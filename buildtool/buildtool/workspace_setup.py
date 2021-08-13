import os
import traceback
from typing import Callable, Dict, List, Optional, Sequence, Set

from colorama import Style

from cache import make_cache_load, make_cache_store
from context import Env
from execution import ExecutionContext
from fs_utils import hash_file
from monitoring import create_status_monitor, log
from state import Rule, TargetLookup
from utils import BuildException, CacheMiss, MissingDependency
from common.hash_utils import HashState


class WorkspaceExecutionContext(ExecutionContext):
    never_defer = True

    def __init__(
        self,
        hashstate: HashState,
        dep_fetcher: Callable[[str], Rule],
    ):
        super().__init__(
            os.curdir,
            os.curdir,
            {},
            hashstate,
            dep_fetcher,
            lambda *args: None,
        )

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

    cache_load_string, _ = make_cache_load(state_directory)
    cache_store_string, _ = make_cache_store(state_directory)

    if work_queue:
        status_monitor = create_status_monitor(1, quiet)
        status_monitor.move(total=len(work_queue))

    def dep_fetcher(dep):
        if dep.startswith(":"):
            if dep not in direct_lookup:
                raise BuildException(f"Unable to find setup rule {dep}")
            dep_rule = direct_lookup[dep]
            log(f"Looking up setup rule {dep}")
            if dep_rule not in ready:
                raise MissingDependency(dep)
            return dep_rule

    while work_queue:
        todo = work_queue.pop()
        log(f"Popping setup rule {todo} off work queue")
        try:
            if todo.name is None:
                raise BuildException(
                    f"All setup rules must have names, but {todo} does not."
                )

            hashstate = HashState()
            ctx = WorkspaceExecutionContext(hashstate, dep_fetcher)
            unchecked_rules = []

            try:
                todo.set_provided_value(
                    todo.impl(ctx),
                    None,
                    ctx.inputs,
                    ctx.deferred_inputs,
                    todo.outputs,
                )
                if ctx.out_of_date_deps:
                    raise MissingDependency(*ctx.out_of_date_deps)
            except MissingDependency as e:
                unchecked_rules = [direct_lookup[x] for x in e.paths]

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
                log(
                    f"Setup rule {todo} ran with inputs {ctx.inputs + ctx.deferred_inputs}"
                )
                for dep in ctx.inputs + ctx.deferred_inputs:
                    if dep.startswith(":"):
                        continue
                    try:
                        hashstate.record(dep)
                        hashstate.update(hash_file(dep))
                    except FileNotFoundError:
                        raise BuildException(f"Source file {dep} not found.")

                try:
                    ok = cache_load_string("workspace", todo.name) == hashstate.state()
                    if not ok:
                        log(f"State mismatch for rule {todo}, need to rerun")
                except CacheMiss:
                    log(f"State not found for rule {todo}, need to run for first time")
                    ok = False

                for dep in ctx.inputs + ctx.deferred_inputs:
                    if dep.startswith(":"):
                        if direct_lookup[dep] in rebuilt:
                            log(
                                f"Dependency {dep} of setup rule {todo} was rebuilt, so we must rebuild {todo} as well"
                            )
                            ok = False

                for out in todo.outputs:
                    if not os.path.exists(out):
                        log(
                            f"Output {out} is missing for setup rule {todo}, forcing rerun"
                        )
                        ok = False
                        break

                if not ok:
                    # we need to fully run
                    log(f"Fully running setup rule {todo}")
                    ctx.run_shell_queue()
                    rebuilt.add(todo)
                    cache_store_string("workspace", todo.name, hashstate.state())

                # either way, now we can trigger our dependents
                ready.add(todo)
                for dep in todo.runtime_dependents:
                    dep.pending_rule_dependencies.remove(todo)
                    if not dep.pending_rule_dependencies:
                        work_queue.append(dep)
                        status_monitor.move(total=1)

            status_monitor.move(curr=1)
        except Exception as e:
            if not isinstance(e, BuildException):
                suffix = f"\n{Style.RESET_ALL}" + traceback.format_exc()
            else:
                suffix = ""
            status_monitor.stop()
            raise BuildException(
                f"Error while executing rule {todo}: " + str(e) + suffix
            )

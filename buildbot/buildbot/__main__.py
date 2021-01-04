from __future__ import annotations

import hashlib
import os
from pathlib import Path
from queue import Queue
from shutil import rmtree
from threading import Lock, Thread
from typing import Collection, Dict, Optional, Set, Union

import click
from execution import ExecutionContext, PreviewContext
from fs_utils import copy_helper, find_root, get_repo_files
from loader import Rule, load_rules
from utils import BuildException, CacheMiss, HashState, MissingDependency


@click.command()
@click.argument("target")
@click.option("--threads", "-t", default=4)
@click.option("--cache-directory", default=".cache")
def cli(target: str, threads: int, cache_directory: str):
    """
    This is a `make` alternative with a simpler syntax and some useful features.
    """
    repo_root = find_root()
    os.chdir(repo_root)

    target_rule_lookup = load_rules()
    all_files = get_repo_files()
    source_files = set(all_files) - target_rule_lookup.keys()

    if target not in target_rule_lookup:
        raise BuildException(f"Target `{target} not found in BUILD files.")
    root_rule = target_rule_lookup[target]

    work_queue: Queue[Optional[Rule]] = Queue()

    ready: Set[Rule] = set()
    scheduled_but_not_ready: Set[Rule] = set()
    scheduling_lock: Lock = Lock()

    def cache_fetcher(state: str, target: str) -> str:
        dest = Path(cache_directory).joinpath(state).joinpath(target)
        try:
            with open(dest, "r") as f:
                return f.read()
        except FileNotFoundError:
            raise CacheMiss

    def enqueue_deps(rule: Rule, candidate_deps: Collection[str]) -> bool:
        waiting_for_deps = False

        with scheduling_lock:
            for dep in candidate_deps:
                if dep in source_files:
                    # nothing to do
                    continue

                if dep not in target_rule_lookup:
                    raise BuildException(f"Unknown dependency {dep}.")
                runtime_dep: Rule = target_rule_lookup[dep]

                if runtime_dep not in ready:
                    waiting_for_deps = True
                    if runtime_dep not in scheduled_but_not_ready:
                        # enqueue dependency
                        scheduled_but_not_ready.add(runtime_dep)
                        work_queue.put(runtime_dep)
                    # register task in the already queued / executing dependency
                    # so when it finishes we may be triggered
                    runtime_dep.runtime_dependents.append(rule)
                    rule.pending_rule_dependencies.append(runtime_dep)
        return waiting_for_deps

    def dep_fetcher(input_path, *, flags="r") -> Union[str, bytes]:
        try:
            if input_path in target_rule_lookup:
                # this input may be stale / unbuilt
                # if so, do not read it, but instead throw MissingDependency
                with scheduling_lock:
                    if input_path not in target_rule_lookup:
                        raise MissingDependency(input_path)
                    if target_rule_lookup[input_path] not in ready:
                        raise MissingDependency(input_path)
                    # so it's already ready for use!

            with open(input_path, flags) as f:
                return f.read()
        except FileNotFoundError:
            raise MissingDependency(input_path)

    def get_deps(rule: Rule):
        """
        Use static dependencies and caches to try and identify as *many*
        needed dependencies as possible, without *any* spurious dependencies.
        """
        hashstate = HashState()
        for dep in rule.deps:
            hashstate.update(dep.encode("utf-8"))
            try:
                with open(dep, "rb") as f:
                    hashstate.update(f.read())
            except FileNotFoundError:
                # get static deps before running the impl!
                break
        else:
            ctx = PreviewContext(
                repo_root,
                rule.location,
                hashstate,
                dep_fetcher,
                cache_fetcher,
            )
            ok = False
            try:
                rule.impl(ctx)
                ok = True
            except CacheMiss:
                pass  # stops context execution
            except MissingDependency:
                pass  # dep already added to ctx.inputs
            # if `ok`, hash loaded dynamic dependencies
            if ok:
                for input_path in ctx.inputs:
                    hashstate.update(input_path.encode("utf-8"))
                    try:
                        data = dep_fetcher(input_path, flags="rb")
                    except MissingDependency:
                        # this dependency was not needed for deps calculation
                        # but is not verified to be up-to-date
                        ok = False
                        break
                    else:
                        with open(input_path, "rb") as f:
                            hashstate.update(data)
            return (
                hashstate.state() if ok else None,
                ctx.inputs + rule.deps,
            )
        return None, rule.deps

    def memorize(state: str, target: str, data: str):
        Path(cache_directory).joinpath(state).joinpath(target).write_text(data)

    def worker(index: int):
        scratch_path = Path(repo_root).joinpath(Path(f".scratch_{index}"))

        def load_deps(deps):
            copy_helper(
                src_root=repo_root, dest_root=scratch_path, src_names=deps, symlink=True
            )

        def build(rule: Rule):
            """
            All the dependencies that can be determined from caches have been
            obtained. Now we need to run. Either we will successfully finish everything,
            or we will get a missing dependency and have to requeue
            """
            load_deps(deps)
            hashstate = HashState()
            for dep in rule.deps:
                hashstate.update(dep.encode("utf-8"))
                with open(dep, "rb") as f:
                    hashstate.update(f.read())
            rule.impl(
                ExecutionContext(
                    scratch_path,
                    scratch_path.joinpath(rule.location),
                    hashstate,
                    load_deps,
                    memorize,
                )
            )
            try:
                copy_helper(
                    src_root=scratch_path,
                    src_names=rule.outputs,
                    dest_root=repo_root,
                )
            except FileNotFoundError as e:
                raise BuildException(
                    f"Output file {e.filename} from rule {todo} was not generated."
                )

        while True:
            todo = work_queue.get()
            if todo is None:
                return

            # only from caches, will never run a subprocess
            cache_key, deps = get_deps(todo)

            if cache_key is None:
                # unable to compute cache_key, potentially because not all deps are ready
                deps_ready = not enqueue_deps(todo, deps)
            else:
                # if the cache_key is ready, *all* the deps must be ready, not just the discoverable deps!
                deps_ready = True

            if deps_ready:
                done = False
                # first check if we're already cached!
                if cache_key:
                    cache_location = Path(cache_directory).joinpath(cache_key)
                    cache_output_names = [
                        hashlib.md5(output_path.encode("utf-8")).hexdigest()
                        for output_path in todo.outputs
                    ]
                    if cache_location.exists():
                        try:
                            copy_helper(
                                src_root=cache_location,
                                src_names=cache_output_names,
                                dest_root=repo_root,
                                dest_names=todo.outputs,
                            )
                        except FileNotFoundError:
                            raise BuildException(
                                "Cache corrupted. This should never happen unless you modified the cache "
                                "directory manually! If so, delete the cache directory and try again."
                            )
                        else:
                            done = True
                    else:
                        # time to execute! but *not* inside the lock
                        # when we release the lock, stuff may change outside, but
                        # we don't care since *our* dependencies (so far) are all available
                        try:
                            build(todo)
                            copy_helper(
                                src_root=scratch_path,
                                dest_root=cache_location,
                                src_names=todo.outputs,
                                dest_names=cache_output_names,
                            )
                            if scratch_path.exists():
                                rmtree(scratch_path)

                            done = True
                        except MissingDependency as d:
                            enqueue_deps(todo, d.paths)

                if done:
                    with scheduling_lock:
                        ready.add(todo)
                        # no one will ever add us back, since we are in `ready`
                        scheduled_but_not_ready.remove(todo)
                        # now it's time to set up our dependents
                        # we need to be inside the lock even if we have no dependents, in case
                        # we *gain* dependents from another thread which could have held the lock!
                        for dependent in todo.runtime_dependents:
                            dependent.pending_rule_dependencies.remove(todo)
                            if not dependent.pending_rule_dependencies:
                                # this guy is ready to go
                                work_queue.put(dependent)

            # either way, we're done with this task for now
            work_queue.task_done()

    scheduled_but_not_ready.add(root_rule)
    work_queue.put(root_rule)

    thread_instances = []
    for i in range(threads):
        thread = Thread(target=worker, args=(i,))
        thread_instances.append(thread)
        thread.start()
    work_queue.join()
    for _ in range(threads):
        work_queue.put(None)
    for thread in thread_instances:
        thread.join()

    if scheduled_but_not_ready:
        # there is a dependency cycle somewhere!
        base = next(iter(scheduled_but_not_ready))
        chain = []
        pos = base
        while True:
            if pos in chain:
                chain.append(pos)
                raise BuildException(
                    f"Circular dependency detected: Rule {pos} depends on itself "
                    f"through the path: {' -> '.join(map(str, chain))}"
                )
            else:
                chain.append(pos)
                pos = pos.pending_rule_dependencies[0]


if __name__ == "__main__":
    cli()

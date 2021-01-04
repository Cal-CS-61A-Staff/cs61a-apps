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


def get_cache_output_paths(cache_directory: str, rule: Rule, cache_key: str):
    cache_location = Path(cache_directory).joinpath(cache_key)
    return cache_location, [
        hashlib.md5(output_path.encode("utf-8")).hexdigest()
        for output_path in rule.outputs
    ]


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
                        print(f"Enqueueing dependency {runtime_dep}")
                        scheduled_but_not_ready.add(runtime_dep)
                        work_queue.put(runtime_dep)
                    else:
                        print(f"Waiting on already queued dependency {runtime_dep}")
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
        print(f"Looking for static dependencies of {rule}")
        for dep in rule.deps:
            if dep in target_rule_lookup:
                with scheduling_lock:
                    if target_rule_lookup[dep] not in ready:
                        print(
                            f"Static dependency {target_rule_lookup[dep]} of {rule} is not ready, skipping impl"
                        )
                        # static deps are not yet ready
                        break
            hashstate.update(dep.encode("utf-8"))
            try:
                dep_fetcher(dep, flags="rb")
                with open(dep, "rb") as f:
                    hashstate.update(f.read())
            except FileNotFoundError:
                # get static deps before running the impl!
                # this means that a source file is *missing*, but the error will be thrown in enqueue_deps
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
                print(f"Running impl of {rule} to discover dynamic dependencies")
                rule.impl(ctx)
                print(f"Impl of {rule} completed with discovered deps: {ctx.inputs}")
                ok = True
            except CacheMiss:
                print(f"Cache miss while running impl of {rule}")
                pass  # stops context execution
            except MissingDependency as e:
                print(
                    f"Dependencies {e.paths} were unavailable while running impl of {rule}"
                )
                pass  # dep already added to ctx.inputs
            # if `ok`, hash loaded dynamic dependencies
            if ok:
                print(
                    f"Runtime dependencies resolved for {rule}, now checking dynamic dependencies"
                )
                for input_path in ctx.inputs:
                    hashstate.update(input_path.encode("utf-8"))
                    try:
                        data = dep_fetcher(input_path, flags="rb")
                    except MissingDependency as e:
                        # this dependency was not needed for deps calculation
                        # but is not verified to be up-to-date
                        ok = False
                        print(
                            f"Dynamic dependencies {e.paths} were not needed for the impl, but are not up to date"
                        )
                        break
                    else:
                        hashstate.update(data)
            return (
                hashstate.state() if ok else None,
                ctx.inputs + rule.deps,
            )
        return None, rule.deps

    def memorize(state: str, target: str, data: str):
        cache_target = Path(cache_directory).joinpath(state).joinpath(target)
        os.makedirs(os.path.dirname(cache_target), exist_ok=True)
        cache_target.write_text(data)

    def worker(index: int):
        scratch_path = Path(repo_root).joinpath(Path(f".scratch_{index}"))
        if scratch_path.exists():
            rmtree(scratch_path)

        def build(rule: Rule):
            """
            All the dependencies that can be determined from caches have been
            obtained. Now we need to run. Either we will successfully finish everything,
            or we will get a missing dependency and have to requeue
            """

            loaded_deps = set()

            def load_deps(deps):
                deps = set(deps) - loaded_deps
                # check that these deps are built! Since they have not been checked by the PreviewExecution.
                missing_deps = []
                for dep in deps:
                    if dep in target_rule_lookup:
                        with scheduling_lock:
                            if target_rule_lookup[dep] not in ready:
                                missing_deps.append(dep)
                if missing_deps:
                    raise MissingDependency(*missing_deps)
                loaded_deps.update(deps)
                print(f"Loading dependencies {deps} into sandbox")
                try:
                    copy_helper(
                        src_root=repo_root,
                        dest_root=scratch_path,
                        src_names=deps,
                        symlink=True,
                    )
                except FileNotFoundError as e:
                    raise BuildException(f"Source file missing: {e.filename}")

            load_deps(deps)
            hashstate = HashState()
            for dep in rule.deps:
                hashstate.update(dep.encode("utf-8"))
                with open(dep, "rb") as f:
                    hashstate.update(f.read())

            ctx = ExecutionContext(
                scratch_path,
                scratch_path.joinpath(rule.location),
                hashstate,
                load_deps,
                memorize,
            )

            rule.impl(ctx)

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

            for input_path in ctx.inputs:
                hashstate.update(input_path.encode("utf-8"))
                with open(input_path, "rb") as f:
                    hashstate.update(f.read())

            return hashstate.state()

        while True:
            todo = work_queue.get()
            if todo is None:
                return

            print(f"Target {todo} popped from queue by worker {i}")

            # only from caches, will never run a subprocess
            cache_key, deps = get_deps(todo)

            if cache_key is None:
                # unable to compute cache_key, potentially because not all deps are ready
                print(
                    f"Target {todo} either has unbuilt dependencies, "
                    f"or does not have a cached dynamic dependency resolved"
                )
                deps_ready = not enqueue_deps(todo, deps)
                if deps_ready:
                    print("Apparently it is missing an input cache in the impl")
                else:
                    print("Apparently it is waiting on unbuilt dependencies")
            else:
                print(f"All the dependencies of target {todo} are ready: {deps}")
                # if the cache_key is ready, *all* the deps must be ready, not just the discoverable deps!
                deps_ready = True

            if deps_ready:
                done = False
                # first check if we're already cached!
                if cache_key:
                    cache_location, cache_output_names = get_cache_output_paths(
                        cache_directory, todo, cache_key
                    )
                    if cache_location.exists():
                        print(f"Target {todo} is in the cache")
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

                if not done:
                    # time to execute! but *not* inside the lock
                    # when we release the lock, stuff may change outside, but
                    # we don't care since *our* dependencies (so far) are all available
                    print(f"Target {todo} is not in the cache, rerunning...")
                    try:
                        cache_key = build(todo)
                        cache_location, cache_output_names = get_cache_output_paths(
                            cache_directory, todo, cache_key
                        )

                        print(
                            f"Target {todo} has been built fully! Caching to {cache_location}"
                        )
                        copy_helper(
                            src_root=scratch_path,
                            dest_root=cache_location,
                            src_names=todo.outputs,
                            dest_names=cache_output_names,
                        )

                        done = True
                    except MissingDependency as d:
                        print(
                            f"Target {todo} failed to fully build because of the missing dynamic "
                            f"dependencies: {d.paths}, requeuing"
                        )
                        enqueue_deps(todo, d.paths)
                    finally:
                        if scratch_path.exists():
                            rmtree(scratch_path)

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

from pathlib import Path
from shutil import rmtree
from subprocess import CalledProcessError

from cache import get_cache_output_paths
from execution import build
from fs_utils import copy_helper
from monitoring import StatusMonitor, log
from preview_execution import get_deps
from utils import BuildException, MissingDependency
from work_queue import enqueue_deps
from build_state import BuildState


def worker(build_state: BuildState, status_monitor: StatusMonitor, index: int):
    scratch_path = Path(build_state.repo_root).joinpath(Path(f".scratch_{index}"))
    if scratch_path.exists():
        rmtree(scratch_path)

    while True:
        todo = build_state.work_queue.get()
        if todo is None:
            return

        try:
            status_monitor.update(index, "Parsing: " + str(todo))

            log(f"Target {todo} popped from queue by worker {index}")

            # only from caches, will never run a subprocess
            cache_key, deps = get_deps(build_state, todo)

            if cache_key is None:
                # unable to compute cache_key, potentially because not all deps are ready
                log(
                    f"Target {todo} either has unbuilt dependencies, "
                    f"or does not have a cached dynamic dependency resolved"
                )
                deps_ready = not enqueue_deps(build_state, todo, deps)
                if deps_ready:
                    log("Apparently it is missing an input cache in the impl")
                else:
                    log("Apparently it is waiting on unbuilt dependencies")
            else:
                log(f"All the dependencies of target {todo} are ready: {deps}")
                # if the cache_key is ready, *all* the deps must be ready, not just the discoverable deps!
                deps_ready = True

            if deps_ready:
                done = False
                # first check if we're already cached!
                if cache_key:
                    cache_location, cache_output_names = get_cache_output_paths(
                        build_state.cache_directory, todo, cache_key
                    )
                    if cache_location.exists():
                        log(f"Target {todo} is in the cache")
                        try:
                            copy_helper(
                                src_root=cache_location,
                                src_names=cache_output_names,
                                dest_root=build_state.repo_root,
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
                    log(f"Target {todo} is not in the cache, rerunning...")
                    status_monitor.update(index, "Building: " + str(todo))
                    try:
                        # if cache_key is None, we haven't finished evaluating the impl, so we
                        # don't know all the dependencies it could need. Therefore, we must
                        # run it in the working directory, so the impl can find the dependencies it needs
                        # Then, we run it *again*, to verify that the dependencies are accurate
                        in_sandbox = cache_key is not None

                        if not in_sandbox:
                            log(
                                f"We don't know the dependencies of {todo}, "
                                f"so we are running the impl in the root directory to find out!"
                            )
                            cache_key = build(
                                build_state, todo, deps, scratch_path=None
                            )
                            # now, if no exception has thrown, all the deps are available to the deps finder
                            alt_cache_key, deps = get_deps(build_state, todo)
                            assert (
                                cache_key == alt_cache_key
                            ), "An internal error has occurred"
                            try:
                                alt_cache_key = build(
                                    build_state,
                                    todo,
                                    deps,
                                    scratch_path=scratch_path,
                                )
                            except MissingDependency:
                                raise BuildException("An internal error has occurred.")
                            except CalledProcessError as e:
                                status_monitor.stop()
                                print(e.cmd)
                                print(e)
                                raise BuildException(
                                    f"The dependencies for target {todo} are not fully specified, "
                                    f"as it failed to build when provided only with them."
                                )
                            assert (
                                cache_key == alt_cache_key
                            ), "An internal error has occurred"
                        else:
                            log(
                                f"We know all the dependencies of {todo}, so we can run it in a sandbox"
                            )
                            build(build_state, todo, deps, scratch_path=scratch_path)
                        cache_location, cache_output_names = get_cache_output_paths(
                            build_state.cache_directory, todo, cache_key
                        )

                        log(
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
                        log(
                            f"Target {todo} failed to fully build because of the missing dynamic "
                            f"dependencies: {d.paths}, requeuing"
                        )
                        scheduled = enqueue_deps(build_state, todo, d.paths)
                        if not scheduled:
                            # due to race conditions, our dependencies are actually all ready now!
                            # no one else will enqueue us, so it is safe to enqueue ourselves
                            build_state.work_queue.put(todo)

                    if scratch_path.exists():
                        rmtree(scratch_path)

                if done:
                    with build_state.scheduling_lock:
                        build_state.ready.add(todo)
                        # no one will ever add us back, since we are in `ready`
                        build_state.scheduled_but_not_ready.remove(todo)
                        # now it's time to set up our dependents
                        # we need to be inside the lock even if we have no dependents, in case
                        # we *gain* dependents from another thread which could have held the lock!
                        for dependent in todo.runtime_dependents:
                            dependent.pending_rule_dependencies.remove(todo)
                            if not dependent.pending_rule_dependencies:
                                # this guy is ready to go
                                build_state.work_queue.put(dependent)

            # either way, we're done with this task for now
            build_state.work_queue.task_done()
        except Exception:
            status_monitor.stop()
            raise

import time
import traceback
from collections import defaultdict
from pathlib import Path
from queue import Empty, Queue
from shutil import rmtree
from subprocess import CalledProcessError

from cache import make_cache_fetcher, make_cache_memorize
from colorama import Style
from execution import build
from monitoring import log
from preview_execution import get_deps
from state import BuildState
from utils import BuildException, MissingDependency
from work_queue import enqueue_deps

TIMINGS = defaultdict(int)


def clear_queue(queue: Queue):
    while not queue.empty():
        try:
            queue.get(False)
        except Empty:
            continue
        queue.task_done()


def worker(build_state: BuildState, index: int):
    scratch_path = Path(build_state.repo_root).joinpath(Path(f".scratch_{index}"))
    if scratch_path.exists():
        rmtree(scratch_path, ignore_errors=True)

    _, cache_save = make_cache_memorize(build_state.cache_directory)
    _, cache_loader = make_cache_fetcher(build_state.cache_directory)

    while True:
        if build_state.failure is not None:
            # every thread needs to clear the queue since otherwise some other thread might still be filling it up
            clear_queue(build_state.work_queue)
            return  # some thread has failed, emergency stop
        todo = build_state.work_queue.get()
        if todo is None:
            return

        start_time = time.time()

        try:
            build_state.status_monitor.update(index, "Parsing: " + str(todo))

            log(f"Target {todo} popped from queue by worker {index}")

            # only from caches, will never run a subprocess
            cache_key, deps, uses_dynamic_deps = get_deps(build_state, todo)

            if uses_dynamic_deps:
                log("Target", todo, "Uses dynamic deps")

            if cache_key is None:
                # unable to compute cache_key, potentially because not all deps are ready
                log(
                    f"Target {todo} either has unbuilt dependencies, "
                    f"or does not have a cached dynamic dependency resolved"
                )
                deps_ready = not enqueue_deps(
                    build_state, todo, deps, catch_failure=uses_dynamic_deps
                )
                if deps_ready:
                    log("Apparently it is missing an input cache in the impl")
                else:
                    log("Apparently it is waiting on unbuilt dependencies")
            else:
                log(f"All the dependencies of target {todo} are ready: {deps}")
                # if the cache_key is ready, *all* the deps must be ready, not just the discoverable deps!
                # unless the cache_key is not actually cached, in which case our inputs() could be wrong, so
                # we have to run in the working directory to verify
                deps_ready = True

            if deps_ready:
                done = False
                # check if we're already cached!
                if cache_key:
                    if cache_loader(cache_key, todo, build_state.repo_root):
                        log(f"Target {todo} was loaded from the cache")
                        done = True

                if not done:
                    # time to execute! but *not* inside the lock
                    # when we release the lock, stuff may change outside, but
                    # we don't care since *our* dependencies (so far) are all available
                    log(f"Target {todo} is not in the cache, rerunning...")
                    build_state.status_monitor.update(index, "Building: " + str(todo))
                    try:
                        # if cache_key is None, we haven't finished evaluating the impl, so we
                        # don't know all the dependencies it could need. Therefore, we must
                        # run it in the working directory, so the impl can find the dependencies it needs
                        # Then, we run it *again*, to verify that the dependencies are accurate
                        in_sandbox = cache_key is not None and not uses_dynamic_deps
                        # if the rule uses_dynamic_deps, then it is possible that a ctx.input() call
                        # in the rule, that was pulled from a cache, will in fact give different outputs
                        # since some dependency has changed. So it is not safe to run it in a sandbox directory,
                        # as the dependencies may not all be ready

                        if not in_sandbox:
                            log(
                                f"We don't know the dependencies of {todo}, "
                                f"so we are running the impl in the root directory to find out!"
                            )
                            cache_key = build(
                                build_state, todo, todo.deps, scratch_path=None
                            )
                            # now, if no exception has thrown, all the deps are available to the deps finder
                            alt_cache_key, deps, _ = get_deps(build_state, todo)
                            try:
                                alt_cache_key_2 = build(
                                    build_state,
                                    todo,
                                    deps,
                                    scratch_path=scratch_path,
                                )
                            except MissingDependency:
                                raise BuildException("An internal error has occurred.")
                            except CalledProcessError as e:
                                build_state.status_monitor.stop()
                                print(e.cmd)
                                print(e)
                                raise BuildException(
                                    f"The dependencies for target {todo} are not fully specified, "
                                    f"as it failed to build when provided only with them."
                                )
                            assert (
                                cache_key == alt_cache_key == alt_cache_key_2
                            ), "An internal error has occurred"
                        else:
                            log(
                                f"We know all the dependencies of {todo}, so we can run it in a sandbox"
                            )
                            build(build_state, todo, deps, scratch_path=scratch_path)
                        log(f"Target {todo} has been built fully!")
                        cache_save(cache_key, todo, scratch_path)

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
                            build_state.status_monitor.move(total=1)

                    if scratch_path.exists():
                        rmtree(scratch_path, ignore_errors=True)

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
                                build_state.status_monitor.move(total=1)

            # either way, we're done with this task for now
            build_state.status_monitor.move(curr=1)
            build_state.work_queue.task_done()

            # record timing data
            run_time = time.time() - start_time
            TIMINGS[str(todo)] += run_time
        except Exception as e:
            if not isinstance(e, BuildException):
                suffix = f"\n{Style.RESET_ALL}" + traceback.format_exc()
            else:
                suffix = ""
            build_state.status_monitor.stop()
            build_state.failure = BuildException(
                f"Error while executing rule {todo}: " + str(e) + suffix
            )
            build_state.work_queue.task_done()

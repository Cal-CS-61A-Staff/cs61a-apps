import os
import time
import traceback
from collections import defaultdict
from pathlib import Path
from queue import Empty, Queue
from shutil import rmtree
from subprocess import CalledProcessError

from cache import make_cache_load, make_cache_store
from colorama import Style
from execution import build
from monitoring import log
from preview_execution import get_deps
from state import BuildState
from utils import BuildException, CacheMiss, MissingDependency
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
    scratch_path = Path(f".scratch_{index}")
    if scratch_path.exists():
        rmtree(scratch_path, ignore_errors=True)

    _, cache_store_files = make_cache_store(build_state.cache_directory)
    _, cache_load_files = make_cache_load(build_state.cache_directory)

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
            (
                cache_key,
                provided_value,
                deps,
                deferred_deps,
                uses_dynamic_deps,
            ) = get_deps(build_state, todo, skip_cache_key=todo.do_not_cache)

            if uses_dynamic_deps:
                log("Target", todo, "Uses dynamic deps")

            if cache_key is None:
                # unable to compute cache_key, potentially because not all deps are ready
                log(
                    f"Target {todo} either has unbuilt dependencies, "
                    f"or does not have a cached dynamic dependency resolved"
                )
                deps_ready = not enqueue_deps(
                    build_state,
                    todo,
                    deps,
                    catch_failure=uses_dynamic_deps,
                )
                if deps_ready:
                    log(f"Apparently {todo} is missing an input cache in the impl")
                else:
                    log(f"Apparently {todo} is waiting on unbuilt dependencies")
            else:
                log(f"All the dependencies of target {todo} are ready: {deps}")
                # if the cache_key is ready, *all* the deps must be ready, not just the discoverable deps!
                # unless the cache_key is not actually cached, in which case our inputs() could be wrong, so
                # we have to run in the working directory to verify
                deps_ready = True

            log(f"Enqueuing deferred dependencies for {todo}: {deferred_deps}")
            enqueue_deps(
                build_state, None, deferred_deps, catch_failure=uses_dynamic_deps
            )

            if deps_ready:
                done = False
                # check if we're already cached!
                if cache_key and not todo.do_not_cache:
                    try:
                        outputs = cache_load_files(cache_key, todo, os.curdir)
                        log(f"Target {todo} was loaded from the cache")
                        done = True
                    except CacheMiss:
                        pass

                if not done:
                    # time to execute! but *not* inside the lock
                    # when we release the lock, stuff may change outside, but
                    # we don't care since *our* dependencies (so far) are all available
                    log(f"Target {todo} is not in the cache, rerunning...")
                    build_state.status_monitor.update(index, "Building: " + str(todo))
                    # if cache_key is None or we use dynamic dependencies, we haven't finished evaluating
                    # the impl, so we don't know all the dependencies it could need. Therefore, we must
                    # run it in the working directory, so the impl can find the dependencies it needs
                    # Then, we run it *again*, to verify that the dependencies are accurate.
                    # The cache_key could be None due to race conditions, even if we don't use dynamic deps.
                    # Imagine:
                    # - Rule A depends on a provider of rule B, which is not yet built
                    #   (and on C, because of B's provider)
                    # - We determine that rule B is not built, so A depends on B but can't complete impl,
                    #   so A.cache_key = None
                    # - B is built
                    # - We try to enqueue the deps of A. Enqueue_deps responds that B is already built,
                    #   so A.deps_ready=True
                    # - So at this stage, A.cache_key = None, A.uses_dynamic_deps=False, but A.deps is missing C!
                    if uses_dynamic_deps or cache_key is None:
                        log(
                            f"We don't know the dependencies of {todo}, "
                            f"so we are running the impl in the root directory to find out!"
                        )

                        try:
                            _, cache_key = build(
                                build_state,
                                todo,
                                scratch_path=None,
                                skip_cache_key=todo.do_not_cache,
                            )
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
                        else:
                            # now, if no exception has thrown, all the deps are available to the deps finder
                            (
                                alt_cache_key,
                                provided_value,
                                deps,
                                deferred_deps,
                                uses_dynamic_deps,
                            ) = get_deps(
                                build_state, todo, skip_cache_key=todo.do_not_cache
                            )
                            try:
                                provided_value, alt_cache_key_2 = build(
                                    build_state,
                                    todo,
                                    scratch_path=scratch_path,
                                    precomputed_deps=deps,
                                    skip_cache_key=todo.do_not_cache,
                                )
                            except CalledProcessError as e:
                                build_state.status_monitor.stop()
                                print(e.cmd)
                                print(e)
                                raise BuildException(
                                    f"The dependencies for target {todo} are not fully specified, "
                                    f"as it failed to build when provided only with them."
                                )
                            if not todo.do_not_cache:
                                assert (
                                    cache_key == alt_cache_key == alt_cache_key_2
                                ), "An internal error has occurred"
                            done = True
                    else:
                        log(
                            f"We know all the dependencies of {todo}, so we can run it in a sandbox"
                        )
                        provided_value, alt_cache_key = build(
                            build_state,
                            todo,
                            scratch_path=scratch_path,
                            precomputed_deps=deps,
                            skip_cache_key=todo.do_not_cache,
                        )
                        if not todo.do_not_cache:
                            assert (
                                cache_key == alt_cache_key
                            ), "An internal error has occurred"
                        done = True

                    if done:
                        log(f"Target {todo} has been built fully!")
                        if not todo.do_not_cache:
                            outputs = cache_store_files(cache_key, todo, os.curdir)
                        else:
                            outputs = []
                            for out in todo.outputs:
                                if out.endswith("/"):
                                    outputs.extend(
                                        os.path.join(path, filename)
                                        for path, subdirs, files in os.walk(out)
                                        for filename in files
                                    )
                                else:
                                    outputs.append(out)

                        if scratch_path.exists():
                            rmtree(scratch_path, ignore_errors=True)

                if done:
                    waiting_for_deferred = enqueue_deps(
                        build_state, todo, deferred_deps
                    )
                    # We have to wait for deferred dependencies to build because the TransitiveOutputProvider
                    # needs them to complete. However, we can run the build itself before the deferred deps finish.
                    if waiting_for_deferred:
                        log(
                            f"Target {todo} has been built, but is waiting for deferred dependencies"
                        )
                    else:
                        todo.set_provided_value(
                            provided_value, build_state, deps, deferred_deps, outputs
                        )
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
            suffix = f"\n{Style.RESET_ALL}" + traceback.format_exc()
            build_state.status_monitor.stop()
            build_state.failure = BuildException(
                f"Error while executing rule {todo}: " + str(e) + suffix
            )
            build_state.work_queue.task_done()

from threading import Thread
from typing import List

from build_worker import worker
from monitoring import create_status_monitor
from state import BuildState
from utils import BuildException


def run_build(
    build_state: BuildState, targets: List[str], num_threads: int, quiet: bool
):
    build_state.status_monitor = create_status_monitor(num_threads, quiet)

    for target in targets:
        root_rule = build_state.target_rule_lookup.try_lookup(
            target
        ) or build_state.target_rule_lookup.lookup(build_state, ":" + target)
        build_state.scheduled_but_not_ready.add(root_rule)
        build_state.work_queue.put(root_rule)
        build_state.status_monitor.move(total=1)

    thread_instances = []
    for i in range(num_threads):
        thread = Thread(target=worker, args=(build_state, i), daemon=True)
        thread_instances.append(thread)
        thread.start()
    build_state.work_queue.join()

    if build_state.failure is not None:
        raise build_state.failure

    for _ in range(num_threads):
        build_state.work_queue.put(None)
    for thread in thread_instances:
        thread.join()

    build_state.status_monitor.stop()

    if build_state.scheduled_but_not_ready:
        # there is a dependency cycle somewhere!
        for root_rule in targets:
            if root_rule in build_state.scheduled_but_not_ready:
                break
        else:
            raise BuildException("An internal error occurred.")
        chain = []
        pos = root_rule
        while True:
            if pos in chain:
                chain.append(pos)
                raise BuildException(
                    f"Circular dependency detected: Rule {pos} depends on itself "
                    f"through the path: {' -> '.join(map(str, chain))}"
                )
            else:
                chain.append(pos)
                pos = next(iter(pos.pending_rule_dependencies))

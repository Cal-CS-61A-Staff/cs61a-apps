from threading import Thread

from build_worker import worker
from monitoring import create_status_monitor
from state import BuildState
from utils import BuildException


def run_build(build_state: BuildState, target: str, num_threads: int):
    root_rule = build_state.target_rule_lookup.try_lookup(
        target
    ) or build_state.target_rule_lookup.lookup(build_state, ":" + target)

    build_state.status_monitor = create_status_monitor(num_threads)

    build_state.scheduled_but_not_ready.add(root_rule)
    build_state.work_queue.put(root_rule)
    build_state.status_monitor.move(total=1)

    thread_instances = []
    for i in range(num_threads):
        thread = Thread(
            target=worker,
            args=(build_state, i),
        )
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
        base = root_rule
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

from __future__ import annotations

from collections import Collection

from build_state import BuildState
from loader import Rule
from monitoring import log
from utils import BuildException


def enqueue_deps(
    build_state: BuildState, rule: Rule, candidate_deps: Collection[str]
) -> bool:
    waiting_for_deps = False

    with build_state.scheduling_lock:
        for dep in candidate_deps:
            if dep in build_state.source_files:
                # nothing to do
                continue

            if dep not in build_state.target_rule_lookup:
                raise BuildException(f"Unknown dependency {dep}.")
            runtime_dep: Rule = build_state.target_rule_lookup[dep]

            if runtime_dep not in build_state.ready:
                waiting_for_deps = True
                if runtime_dep not in build_state.scheduled_but_not_ready:
                    # enqueue dependency
                    log(f"Enqueueing dependency {runtime_dep}")
                    build_state.scheduled_but_not_ready.add(runtime_dep)
                    build_state.work_queue.put(runtime_dep)
                else:
                    log(f"Waiting on already queued dependency {runtime_dep}")
                # register task in the already queued / executing dependency
                # so when it finishes we may be triggered
                runtime_dep.runtime_dependents.append(rule)
                rule.pending_rule_dependencies.append(runtime_dep)
    return waiting_for_deps

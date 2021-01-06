from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from queue import Queue
from threading import Lock
from typing import Callable, Dict, List, Optional, Sequence, Set

from context import Context
from monitoring import StatusMonitor
from utils import BuildException


@dataclass
class BuildState:
    # config parameters
    cache_directory: str
    target_rule_lookup: TargetLookup
    source_files: Set[str]
    repo_root: str

    # logging
    status_monitor: StatusMonitor = None

    # dynamic state
    scheduling_lock: Lock = field(default_factory=Lock)
    ready: Set[Rule] = field(default_factory=set)
    scheduled_but_not_ready: Set[Rule] = field(default_factory=set)
    work_queue: Queue[Optional[Rule]] = field(default_factory=Queue)
    failure: Optional[BuildException] = None


@dataclass
class TargetLookup:
    direct_lookup: Dict[str, Rule] = field(default_factory=dict)
    location_lookup: Dict[str, Rule] = field(default_factory=dict)

    def lookup(self, build_state: BuildState, dep: str) -> Rule:
        if dep in build_state.source_files:
            raise BuildException(
                f"Dependency {dep} is a source file, not a buildable dependency. "
                f"This is likely an internal error."
            )
        else:
            rule = self.try_lookup(dep)
            if rule is None:
                raise BuildException(f"Unable to resolve dependency {dep}")
            return rule

    def try_lookup(self, dep: str) -> Optional[Rule]:
        if dep in self.direct_lookup:
            return self.direct_lookup[dep]
        else:
            # check locations
            for parent in Path(dep).parents:
                key = str(parent) + "/"
                if key in self.location_lookup:
                    return self.location_lookup[key]

    def find_source_files(self, all_files: List[str]) -> Set[str]:
        out = set(all_files)
        for file in all_files:
            if self.try_lookup(file) is not None:
                out.remove(file)
        return out

    def verify(self):
        # check for overlaps involving location_lookups
        for path in list(self.direct_lookup) + list(self.location_lookup):
            # check that this path does not lie inside a parent, by checking all prefixes
            for parent in Path(path).parents:
                key = str(parent) + "/"
                if key in self.location_lookup:
                    raise BuildException(
                        f"Outputs {key} and {path} overlap - all outputs must be disjoint"
                    )


@dataclass(eq=False)
class Rule:
    name: Optional[str]
    location: str
    deps: Sequence[str]
    impl: Callable[[Context], None]
    outputs: Sequence[str]

    runtime_dependents: List[Rule] = field(default_factory=list)
    pending_rule_dependencies: List[Rule] = field(default_factory=list)

    def __hash__(self):
        return hash(id(self))

    def __str__(self):
        if self.name:
            return f":{self.name}"
        elif len(self.outputs) == 1:
            return self.outputs[0]
        else:
            return f"<anonymous rule from {self.location}/BUILD>"

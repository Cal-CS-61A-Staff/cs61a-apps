from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from queue import Queue
from threading import Lock
from typing import Callable, Dict, List, Optional, Sequence, Set

from context import Context
from monitoring import StatusMonitor
from providers import (
    AbstractProvider,
    DepsProvider,
    IterableDepSet,
    OutputProvider,
    TransitiveDepsProvider,
    TransitiveOutputProvider,
)
from utils import BuildException


@dataclass
class BuildState:
    # config parameters
    cache_directory: str
    target_rule_lookup: TargetLookup
    source_files: SourceFileLookup
    macros: Dict[str, Callable]

    # logging
    status_monitor: StatusMonitor = None

    # dynamic state
    scheduling_lock: Lock = field(default_factory=Lock)
    ready: Set[Rule] = field(default_factory=set)
    scheduled_but_not_ready: Set[Rule] = field(default_factory=set)
    work_queue: Queue[Optional[Rule]] = field(default_factory=Queue)
    failure: Optional[BuildException] = None


@dataclass
class SourceFileLookup:
    tracked_files: Set[str]
    cached_contains: Dict[str, bool] = field(default_factory=dict)

    def __contains__(self, dep):
        if dep not in self.cached_contains:
            self.cached_contains[dep] = (dep in self.tracked_files) or (
                os.path.relpath(os.path.realpath(dep), os.curdir) in self.tracked_files
            )
        return self.cached_contains[dep]


@dataclass
class TargetLookup:
    direct_lookup: Dict[str, Rule] = field(default_factory=dict)
    location_lookup: Dict[str, Rule] = field(default_factory=dict)

    def __iter__(self):
        yield from self.direct_lookup
        yield from self.location_lookup

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

    def find_source_files(self, all_files: List[str]) -> SourceFileLookup:
        out = set(all_files)
        for file in all_files:
            if self.try_lookup(file) is not None:
                out.remove(file)
        return SourceFileLookup(out)

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
    impl: Callable[[Context], None]
    outputs: Sequence[str]

    # advanced config
    do_not_symlink: bool
    do_not_cache: bool

    runtime_dependents: Set[Rule] = field(default_factory=set, repr=False)
    pending_rule_dependencies: Set[Rule] = field(default_factory=set, repr=False)
    _provided_value: Dict[AbstractProvider, object] = None

    def __hash__(self):
        return hash(id(self))

    def __str__(self):
        if self.name:
            return f":{self.name}"
        elif len(self.outputs) == 1:
            return self.outputs[0]
        else:
            return f"<anonymous rule from {self.location}/BUILD>"

    @property
    def provided_value(self):
        return self._provided_value

    def set_provided_value(
        self,
        value: Optional[List[AbstractProvider]],
        build_state: Optional[BuildState],
        deps: List[str],
        deferred_deps: List[str],
        outputs: List[str],
    ):
        if value is not None and (
            not isinstance(value, list)
            or not all(isinstance(x, AbstractProvider) for x in value)
        ):
            raise BuildException(
                f"Build rules can only return a list of Providers (or None), received {value}"
            )

        self._provided_value = {
            DepsProvider: IterableDepSet(*deps),
            OutputProvider: IterableDepSet(*outputs),
            **(
                {
                    TransitiveDepsProvider: IterableDepSet(
                        *deps,
                        *(
                            dep
                            if dep in build_state.source_files
                            else build_state.target_rule_lookup.lookup(
                                build_state, dep
                            ).provided_value[TransitiveDepsProvider]
                            for dep in (deps + deferred_deps)
                            if dep not in build_state.source_files
                        ),
                    ),
                    TransitiveOutputProvider: IterableDepSet(
                        *outputs,
                        *(
                            build_state.target_rule_lookup.lookup(
                                build_state, dep
                            ).provided_value[TransitiveOutputProvider]
                            for dep in (deps + deferred_deps)
                            if dep not in build_state.source_files
                        ),
                    ),
                }
                if build_state is not None
                else {}
            ),
            **{type(x): x.value for x in value or {}},
        }

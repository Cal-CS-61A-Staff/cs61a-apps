from __future__ import annotations

from dataclasses import dataclass, field
from queue import Queue
from threading import Lock
from typing import Dict, Optional, Set

from loader import Rule
from monitoring import StatusMonitor


@dataclass
class BuildState:
    # config parameters
    cache_directory: str
    target_rule_lookup: Dict[str, Rule]
    source_files: Set[str]
    repo_root: str

    # logging
    status_monitor: StatusMonitor = None

    # dynamic state
    scheduling_lock: Lock = field(default_factory=Lock)
    ready: Set[Rule] = field(default_factory=set)
    scheduled_but_not_ready: Set[Rule] = field(default_factory=set)
    work_queue: Queue[Optional[Rule]] = field(default_factory=Queue)

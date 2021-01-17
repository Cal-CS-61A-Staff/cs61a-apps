from dataclasses import dataclass
from sys import stderr
from threading import Lock
from typing import Callable, Protocol

from tqdm import tqdm


def enable_logging():
    log.enabled = True


def enable_profiling():
    log.profile = True


def log(*args):
    if log.enabled:
        print(*args, file=stderr)
    elif args[0].startswith("RUNNING") and log.profile:
        print(*args, file=stderr)


log.enabled = False
log.profile = False


class MoveCallable(Protocol):
    def __call__(self, *, curr: int = None, total: int = None) -> None:
        ...


@dataclass
class StatusMonitor:
    update: Callable[[int, str], None]
    move: MoveCallable
    stop: Callable[[], None]


def create_status_monitor(num_threads: int, quiet: bool):
    status = ["IDLE"] * num_threads

    bar = tqdm(total=0, disable=quiet)
    lock = Lock()
    pos = 0
    tot = 0

    def update(index: int, msg: str):
        status[index] = msg
        # with lock:
        #     bar.set_description(", ".join(status))

    def move(*, curr: int = None, total: int = None):
        nonlocal pos, tot
        with lock:
            if curr is not None:
                pos += curr
                bar.update(curr)
            if total is not None:
                tot += total
                bar.total = tot
                bar.refresh()
        bar.set_description(str((pos, tot)))

    def stop():
        bar.close()

    return StatusMonitor(update, move, stop)

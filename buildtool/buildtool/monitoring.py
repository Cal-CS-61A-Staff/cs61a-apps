from dataclasses import dataclass
from typing import Callable

from asciimatics.screen import Screen


def log(*args):
    pass


@dataclass
class StatusMonitor:
    update: Callable[[int, str], None]
    stop: Callable[[], None]


def create_status_monitor(num_threads: int):
    status = ["IDLE"] * num_threads

    screen = Screen.open()

    def update(index: int, msg: str):
        status[index] = msg
        screen.clear()
        for i, msg in enumerate(status):
            screen.print_at(msg, 0, i)
        screen.refresh()

    def stop():
        screen.close(restore=True)

    return StatusMonitor(update, stop)

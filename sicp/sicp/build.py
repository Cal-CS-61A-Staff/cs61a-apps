import os
import time
from typing import Union

import click
from crcmod.crcmod import _usingExtension
from crcmod.predefined import mkPredefinedCrcFun
from watchdog.events import (
    DirMovedEvent,
    FileMovedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

from sicp.common.shell_utils import sh

# TODO: Properly indicate if the extension is not installed
from sicp.examtool.api.auth import get_token, set_token_path

TARGET = "/Users/rahularya/PyCharmProjects/berkeley-cs61a"

DOES_NOT_EXIST = "DOES_NOT_EXIST"


@click.command()
def build():
    os.chdir(TARGET)
    set_token_path(".token")
    hash_all()
    observer = Observer()
    observer.schedule(Handler(), TARGET, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


class Handler(FileSystemEventHandler):
    def on_any_event(self, event: FileSystemEvent):
        synchronize(event.src_path)

    def on_moved(self, event: Union[DirMovedEvent, FileMovedEvent]):
        synchronize(event.dest_path)


def synchronize(path: str):
    token = get_token()


def get_hash(path):
    assert _usingExtension, "You must use the crcmod C extension"
    hash_func = mkPredefinedCrcFun("crc-32")
    try:
        with open(path, "rb") as f:
            return hash_func(f.read())
    except FileNotFoundError:
        return DOES_NOT_EXIST
    except IsADirectoryError:
        return


def hash_all():
    files = sh("git", "ls-files", capture_output=True, quiet=True).splitlines()
    for file in files:
        get_hash(file)

import os
import time
import traceback
from base64 import b64encode
from os.path import relpath
from typing import Union

import click
from crcmod.crcmod import _usingExtension
from crcmod.predefined import mkPredefinedCrcFun
from tqdm import tqdm
from watchdog.events import (
    DirMovedEvent,
    FileMovedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

from common.rpc.auth_utils import set_token_path
from common.rpc.sandbox import (
    get_server_hashes,
    initialize_sandbox,
    is_sandbox_initialized,
    run_incremental_build,
    update_file,
)
from common.shell_utils import sh

# TODO: Properly indicate if the extension is not installed

TARGET = "/Users/rahularya/PyCharmProjects/berkeley-cs61a"

SYMLINK = "SYMLINK"

internal_hashmap = {}

do_build = True


@click.command()
def build():
    global internal_hashma, do_build
    os.chdir(TARGET)
    set_token_path(".token")
    if not is_sandbox_initialized():
        print("Sandbox is not initialized.")
        if click.confirm(
            "Do you want to initialize your sandbox? It will take about 10 minutes."
        ):
            initialize_sandbox()
        else:
            return
    print("Scanning local directory...")
    synchronize_from(get_server_hashes, show_progress=True)
    while True:
        observer = Observer()
        try:
            observer.schedule(Handler(), TARGET, recursive=True)
            observer.start()
            for _ in range(15):
                time.sleep(1)
                if do_build:
                    do_build = False
                    run_incremental_build()
            full_synchronization()
        finally:
            observer.stop()
            observer.join()


class Handler(FileSystemEventHandler):
    def on_any_event(self, event: FileSystemEvent):
        synchronize(event.src_path)

    def on_moved(self, event: Union[DirMovedEvent, FileMovedEvent]):
        synchronize(event.dest_path)


def synchronize(path: str):
    global do_build
    os.chdir(TARGET)
    path = relpath(path)
    if isinstance(path, bytes):
        path = path.decode("ascii")
    print("Synchronizing " + path)
    try:
        # path is a path to either a file or a symlink, NOT a directory
        if os.path.islink(path):
            print("Path is a symlink " + path)
            update_file(path=path, symlink=os.readlink(path))
        elif os.path.isfile(path):
            with open(path, "rb") as f:
                update_file(
                    path=path, encoded_file_contents=b64encode(f.read()).decode("ascii")
                )
        elif not os.path.exists(path):
            update_file(path=path, delete=True)
        internal_hashmap[path] = get_hash(path)
        do_build = True
    except Exception as e:
        raise
        traceback.print_exc()
        os._exit(1)


def full_synchronization():
    synchronize_from(internal_hashmap)


def synchronize_from(remote_state, show_progress=False):
    global internal_hashmap
    current_state = hash_all(show_progress=show_progress)
    if callable(remote_state):
        # When we want to fetch it lazily
        if show_progress:
            print("Fetching server state...")
        remote_state = remote_state()
    paths = set(current_state) | set(remote_state)
    to_update = []
    for path in paths:
        if current_state.get(path) != remote_state.get(path):
            to_update.append(path)

    for path in tqdm(to_update) if show_progress else to_update:
        print(
            "Synchronizing, curr={}, remote={}",
            current_state.get(path),
            remote_state.get(path),
        )
        synchronize(path)

    internal_hashmap = current_state


def get_hash(path):
    assert _usingExtension, "You must use the crcmod C extension"
    if isinstance(path, bytes):
        path = path.decode("ascii")
    hash_func = mkPredefinedCrcFun("crc-32")
    if os.path.islink(path):
        return SYMLINK + os.readlink(path)
    try:
        with open(path, "rb") as f:
            return hash_func(f.read())
    except FileNotFoundError:
        return
    except IsADirectoryError:
        return


def hash_all(show_progress=False):
    files = (
        sh(
            "git", "ls-files", "--exclude-standard", capture_output=True, quiet=True
        ).splitlines()  # All tracked files
        + sh(
            "git",
            "ls-files",
            "-o",
            "--exclude-standard",
            capture_output=True,
            quiet=True,
        ).splitlines()  # Untracked but not ignored files
    )
    out = {}
    for file in tqdm(files) if show_progress else files:
        h = get_hash(file)
        if isinstance(file, bytes):
            file = file.decode("ascii")
        out[relpath(file)] = h
    return out

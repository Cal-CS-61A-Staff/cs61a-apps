import os
import pathlib
import sys
import time
import webbrowser
from base64 import b64encode
from os.path import relpath
from threading import Thread
from typing import Union

import click
import requests
from cachetools import LRUCache
from colorama import Fore, Style
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

from common.cli_utils import pretty_print
from common.rpc.auth_utils import get_token
from common.rpc.sandbox import (
    get_server_hashes,
    initialize_sandbox,
    is_sandbox_initialized,
    run_make_command,
    update_file,
)
from common.shell_utils import sh

# TODO: Properly indicate if the extension is not installed


REPO = "berkeley-cs61a"

SYMLINK = "SYMLINK"
SUCCESS = "SUCCESS"

tracked_files = set()
remote_state = {}
recent_files = LRUCache(15)
do_build = True


def find_target():
    if not hasattr(find_target, "out"):
        remote = sh(
            "git",
            "config",
            "--get",
            "remote.origin.url",
            capture_output=True,
            quiet=True,
        ).decode("utf-8")
        if REPO not in remote:
            raise Exception(
                "You must run this command in the berkeley-cs61a repo directory"
            )
        find_target.out = (
            sh("git", "rev-parse", "--show-toplevel", capture_output=True, quiet=True)
            .decode("utf-8")
            .strip()
        )
    return find_target.out


def get_sandbox_url():
    username = requests.get(
        "https://okpy.org/api/v3/user/", params={"access_token": get_token()}
    ).json()["data"]["email"][: -len("@berkeley.edu")]
    return f"https://{username}.sb.cs61a.org"


@click.command()
def build():
    os.chdir(find_target())
    if not is_sandbox_initialized():
        print("Sandbox is not initialized.")
        if click.confirm(
            "You need to initialize your sandbox first. Continue?", default=True
        ):
            initialize_sandbox()
            for line in run_make_command(target="virtualenv"):
                print(line, end="")
            print()
        else:
            return
    print("Please wait until synchronization completes...")
    print("Scanning local directory...")
    full_synchronize_with_remote(get_server_hashes, show_progress=True)
    sandbox_url = get_sandbox_url()
    print(
        f"Synchronization completed! You can now begin developing. Preview your changes at {sandbox_url}"
    )
    webbrowser.open(sandbox_url)

    Thread(target=catchup_synchronizer_thread, daemon=True).start()
    Thread(target=catchup_full_synchronizer_thread, daemon=True).start()
    Thread(target=file_events_thread, daemon=True).start()

    # run this thread on the main thread to handle KeyboardInterrupts
    input_thread()


def input_thread():
    try:
        import readline
    except ImportError:
        # todo: use pyreadline on windows
        pass

    try:
        while True:
            print(Style.BRIGHT, end="")
            target = input("make> ")
            print(Style.RESET_ALL, end="")
            if not target.strip():
                continue
            try:
                for line in run_make_command(target=target):
                    print(line, end="")
            except KeyboardInterrupt:
                print(Fore.RED)
                pretty_print("🚫", "Build cancelled.")
            except Exception as e:
                print(Fore.RED)
                print(str(e))
                pretty_print("😿", "Build failed.")
            else:
                print(Fore.GREEN)
                pretty_print("🎉", "Build completed!")
    except KeyboardInterrupt:
        pretty_print("👋", "Interrupt signal received, have a nice day!")
        sys.exit(0)


def file_events_thread():
    while True:
        observer = Observer()
        try:
            observer.schedule(Handler(), find_target(), recursive=True)
            observer.start()
            for _ in range(15):
                time.sleep(1)
        finally:
            observer.stop()
            observer.join()


def catchup_synchronizer_thread():
    while True:
        recent_synchronization()
        time.sleep(1)


def catchup_full_synchronizer_thread():
    while True:
        full_synchronize_with_remote()
        time.sleep(15)


class Handler(FileSystemEventHandler):
    def on_any_event(self, event: FileSystemEvent):
        synchronize(event.src_path)

    def on_moved(self, event: Union[DirMovedEvent, FileMovedEvent]):
        synchronize(event.dest_path)


def synchronize(path: str):
    os.chdir(find_target())
    path = relpath(path)
    if isinstance(path, bytes):
        path = path.decode("ascii")
    if path not in tracked_files:
        # do not synchronize untracked files
        # if this is a file just created, it will be tracked on the next full_synchronization pass
        return
    recent_files[path] = None
    # path is a path to either a file or a symlink, NOT a directory
    if os.path.islink(path):
        update_file(path=path, symlink=os.readlink(path))
    elif os.path.isfile(path):
        with open(path, "rb") as f:
            update_file(
                path=path, encoded_file_contents=b64encode(f.read()).decode("ascii")
            )
    elif not os.path.exists(path):
        update_file(path=path, delete=True)
    remote_state[path] = get_hash(path)


def recent_synchronization():
    for path in set(recent_files.keys()):  # set() is needed to avoid concurrency issues
        if remote_state.get(path) != get_hash(path):
            synchronize(path)


def full_synchronize_with_remote(remote_state_getter=None, show_progress=False):
    global remote_state
    current_state = hash_all(show_progress=show_progress)
    if callable(remote_state_getter):
        # When we want to fetch it lazily
        if show_progress:
            print("Fetching server state...")
        remote_state = remote_state_getter()
    paths = set(current_state) | set(remote_state)
    to_update = []
    for path in paths:
        if current_state.get(path) != remote_state.get(path):
            to_update.append(path)

    for path in tqdm(to_update) if show_progress else to_update:
        synchronize(path)

    remote_state = current_state


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
    global tracked_files
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
    tracked_files = set(out) | set(remote_state)
    return out

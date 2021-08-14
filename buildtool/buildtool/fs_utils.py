import hashlib
import os
from functools import lru_cache
from pathlib import Path
from shutil import SameFileError, copyfile, copytree
from typing import List

from common.shell_utils import sh
from utils import BuildException


def find_root():
    repo_root = os.path.abspath(os.path.curdir)
    while True:
        if "WORKSPACE" in os.listdir(repo_root):
            return repo_root
        repo_root = os.path.dirname(repo_root)
        if repo_root == os.path.dirname(repo_root):
            break
    raise BuildException(
        "Unable to find WORKSPACE file - are you in the project directory?"
    )


@lru_cache()
def get_repo_files() -> List[str]:
    return [
        file.decode("ascii") if isinstance(file, bytes) else file
        for file in sh(
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
    ]


@lru_cache(None)
def normalize_path(build_root, path):
    path = str(path)
    suffix = "/" if path.endswith("/") else ""
    if path.startswith("//"):
        path = os.path.normpath(path[2:])
    else:
        path = os.path.normpath(os.path.join(build_root, path))
    if ".." in path or path.startswith("/"):
        raise BuildException(
            f"Target `{path}` is not in the root directory of the repo."
        )
    return path + suffix


def copy_helper(*, src_root, dest_root, src_names, dest_names=None, symlink=False):
    if not dest_names:
        dest_names = src_names
    assert len(src_names) == len(dest_names)
    srcs = []
    dests = []
    for src_name, dest_name in zip(src_names, dest_names):
        src = Path(src_root).joinpath(src_name)
        dest = Path(dest_root).joinpath(dest_name)
        if os.path.dirname(dest):
            os.makedirs(os.path.dirname(dest), exist_ok=True)
        try:
            if symlink:
                Path(dest).symlink_to(os.path.abspath(src))
                srcs.append(src_name)
                dests.append(dest_name)
            elif src_name.endswith("/"):
                copytree(src=src, dst=dest, dirs_exist_ok=True)
                for acc, dir in zip([srcs, dests], [src, dest]):
                    acc.extend(
                        os.path.join(path, filename)
                        for path, subdirs, files in os.walk(dir)
                        for filename in files
                    )
            else:
                copyfile(src, dest)
                srcs.append(src_name)
                dests.append(dest_name)
        except SameFileError:
            pass
    return srcs, dests


def hash_file(path):
    # only hash files whose contents are "locked in". That way we can cache safely.
    if path in hash_file.cache:
        return hash_file.cache[path]
    else:
        with open(path, "rb") as f:
            out = hash_file.cache[path] = (
                hashlib.md5(f.read()).hexdigest().encode("utf-8")
            )
            return out


hash_file.cache = {}

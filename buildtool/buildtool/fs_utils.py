import hashlib
import os
from functools import lru_cache
from pathlib import Path
from shutil import SameFileError, copyfile, copytree
from typing import List

from utils import BuildException

from common.shell_utils import sh


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


def normalize_path(repo_root, build_root, path):
    suffix = "/" if path.endswith("/") else ""
    if path.startswith("//"):
        path = Path(repo_root).joinpath(path[2:])
    else:
        path = Path(repo_root).joinpath(build_root, path)
    path = Path(os.path.abspath(path))
    repo_root = Path(os.path.abspath(repo_root))
    if repo_root != path and repo_root not in path.parents:
        raise BuildException(
            f"Target `{path}` is not in the root directory of the repo."
        )
    return str(path.relative_to(repo_root)) + suffix


def copy_helper(*, src_root, dest_root, src_names, dest_names=None, symlink=False):
    if not dest_names:
        dest_names = src_names
    assert len(src_names) == len(dest_names)
    for src_name, dest_name in zip(src_names, dest_names):
        src = Path(src_root).joinpath(src_name)
        dest = Path(dest_root).joinpath(dest_name)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        try:
            if symlink:
                Path(dest).symlink_to(src)
            elif src_name.endswith("/"):
                copytree(src=src, dst=dest, dirs_exist_ok=True)
            else:
                copyfile(src, dest)
        except SameFileError:
            pass


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

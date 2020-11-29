import os
import subprocess
import sys
from contextlib import contextmanager
from shutil import rmtree
from typing import List


def sh(*args, env={}, capture_output=False, quiet=False):
    if quiet:
        out = subprocess.run(
            args, env={**os.environ, **env, "ENV": "dev"}, stdout=subprocess.PIPE
        )
    else:
        out = subprocess.run(
            args, env={**os.environ, **env, "ENV": "dev"}, capture_output=capture_output
        )
    if capture_output and not quiet:
        print(out.stdout, file=sys.stdout)
        print(out.stderr, file=sys.stderr)
    out.check_returncode()
    return out.stdout


def clean_all_except(folders: List[str]):
    for dirpath, _, filenames in os.walk("."):
        dirnames = dirpath.split(os.sep)[1:]
        if not dirnames:
            for filename in filenames:
                os.remove(filename)
        elif dirnames[0] not in folders:
            rmtree(dirpath)


@contextmanager
def tmp_directory(*, clean=False):
    main_dir = os.getcwd()
    if clean:
        sh("rm", "-rf", "tmp")
        os.mkdir("tmp")
    try:
        os.chdir("tmp")
        yield None
    finally:
        os.chdir(main_dir)

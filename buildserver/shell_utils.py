import os
import subprocess
import sys
from contextlib import contextmanager


def sh(*args, capture_output=False):
    out = subprocess.run(args, env={**os.environ, "ENV": "dev"}, capture_output=capture_output)
    if capture_output:
        print(out.stdout, file=sys.stdout)
        print(out.stderr, file=sys.stderr)
    out.check_returncode()
    return out.stdout


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

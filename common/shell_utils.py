import os
import subprocess
import sys
from contextlib import contextmanager
from shutil import rmtree
from typing import List


def sh(*args, env={}, capture_output=False, stream_output=False, quiet=False):
    assert not (
        capture_output and stream_output
    ), "Cannot both capture and stream output"

    env = {**os.environ, **env, "ENV": "dev"}
    if stream_output:
        out = subprocess.Popen(
            args,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
        )

        def generator():
            while True:
                line = out.stdout.readline()
                yield line
                returncode = out.poll()
                if returncode is not None:
                    if returncode != 0:
                        # This exception will not be passed to the RPC handler, so we need
                        # to handle it ourselves
                        raise subprocess.CalledProcessError(returncode, args, "", "")
                    else:
                        return ""

        return generator()
    elif capture_output:
        out = subprocess.run(args, env=env, capture_output=capture_output)
    else:
        out = subprocess.run(args, env=env, stdout=subprocess.PIPE)
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

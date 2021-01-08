import os
import subprocess
import sys
from contextlib import contextmanager
from io import BytesIO
from shutil import rmtree
from typing import List, TextIO, Union
from typing.io import IO


def sh(
    *args,
    env={},
    capture_output=False,
    stream_output=False,
    quiet=False,
    shell=False,
    cwd=None,
    inherit_env=True,
):
    assert not (
        capture_output and stream_output
    ), "Cannot both capture and stream output"

    if shell:
        args = [" ".join(args)]

    if inherit_env:
        env = {**os.environ, **env, "ENV": "dev"}

    if stream_output:
        out = subprocess.Popen(
            args,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
            shell=shell,
            cwd=cwd,
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
        out = subprocess.run(
            args, env=env, capture_output=capture_output, shell=shell, cwd=cwd
        )
    else:
        out = subprocess.run(
            args, env=env, stdout=subprocess.PIPE, shell=shell, cwd=cwd
        )
    if capture_output and not quiet:
        print(out.stdout.decode("utf-8"), file=sys.stdout)
        print(out.stderr.decode("utf-8"), file=sys.stderr)
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


@contextmanager
def redirect_descriptor(
    src: Union[IO, TextIO, BytesIO], target: Union[IO, TextIO, BytesIO]
):
    src_fd: int = src.fileno()
    with os.fdopen(os.dup(src_fd), "wb") as saved:
        src.flush()
        os.dup2(target.fileno(), src_fd)
        try:
            yield src
        finally:
            src.flush()
            os.dup2(saved.fileno(), src_fd)

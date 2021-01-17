from time import sleep
from typing import List

import click

from common.cli_utils import pretty_print
from common.shell_utils import sh


def fetch_out_of_date_pages() -> List[str]:
    # rpc goes here
    ...


def run_build(targets, flags):
    sh(
        "buildtool",
        "--shell-log",
        "--quiet",
        *targets,
        *[arg for flag in flags for arg in ("--flag", flag)],
    )


@click.command()
@click.option("--flag", "-f", "flags", type=str, multiple=True)
def watch(flags):
    """
    File watcher intended to be run on ide.cs61a.org, to automatically rebuild
    the sandbox preview
    """
    pretty_print("", "Verifying WORKSPACE...")
    run_build(["--skip-build"], flags)
    pretty_print("🎉", "WORKSPACE verified! Auto-rebuilder activated.")
    while True:
        targets = fetch_out_of_date_pages()
        if targets:
            run_build(["--skip-setup", *targets], flags)
        else:
            sleep(2)

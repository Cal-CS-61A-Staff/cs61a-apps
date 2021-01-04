from __future__ import annotations

import os
from threading import Thread

import click
from build_coordinator import run_build
from build_worker import worker
from fs_utils import find_root, get_repo_files
from loader import load_rules
from monitoring import create_status_monitor
from utils import BuildException
from build_state import BuildState


@click.command()
@click.argument("target")
@click.option("--threads", "-t", default=8)
@click.option("--cache-directory", default=".cache")
def cli(target: str, threads: int, cache_directory: str):
    """
    This is a `make` alternative with a simpler syntax and some useful features.
    """
    repo_root = find_root()
    os.chdir(repo_root)

    target_rule_lookup = load_rules()
    all_files = get_repo_files()
    source_files = set(all_files) - target_rule_lookup.keys()

    run_build(
        BuildState(
            target_rule_lookup=target_rule_lookup,
            source_files=source_files,
            cache_directory=cache_directory,
            repo_root=repo_root,
        ),
        target,
        threads,
    )


if __name__ == "__main__":
    cli()

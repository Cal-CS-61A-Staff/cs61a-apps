from __future__ import annotations

import os

import click
from colorama import Fore, Style

from build_coordinator import run_build
from common.cli_utils import pretty_print
from state import BuildState
from fs_utils import find_root, get_repo_files
from loader import load_rules
from utils import BuildException


def display_error(error: BuildException):
    print(Fore.RED)
    pretty_print("🚫", "Build failed.")
    print(Style.BRIGHT)
    print(error)
    exit(1)


@click.command()
@click.argument("target")
@click.option("--threads", "-t", default=8)
@click.option("--cache-directory", default=".cache")
def cli(target: str, threads: int, cache_directory: str):
    """
    This is a `make` alternative with a simpler syntax and some useful features.
    """
    try:
        repo_root = find_root()
        os.chdir(repo_root)

        target_rule_lookup = load_rules()
        target_rule_lookup.verify()
        all_files = get_repo_files()
        source_files = target_rule_lookup.find_source_files(all_files)

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
    except BuildException as e:
        display_error(e)
    except Exception as e:
        display_error(BuildException("Error while processing rules: " + repr(e)))


if __name__ == "__main__":
    cli()

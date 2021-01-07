from __future__ import annotations

import os
import traceback
from json import loads
from typing import List

import click
from colorama import Fore, Style

from build_coordinator import run_build
from build_worker import TIMINGS as BUILD_TIMINGS
from common.cli_utils import pretty_print
from state import BuildState
from fs_utils import find_root, get_repo_files
from loader import load_rules, TIMINGS as LOAD_TIMINGS
from utils import BuildException


def display_error(error: BuildException):
    print(Fore.RED)
    pretty_print("🚫", "Build failed.")
    print(Style.BRIGHT)
    print(error)


@click.command()
@click.argument("target")
@click.option("--profile", "-p", default=False, is_flag=True)
@click.option("--locate", "-l", default=False, is_flag=True)
@click.option("--threads", "-t", default=8)
@click.option("--cache-directory", default=".cache")
@click.option("--flag", "-f", type=str, multiple=True)
def cli(
    target: str,
    profile: bool,
    locate: bool,
    threads: int,
    cache_directory: str,
    flag: List[str],
):
    """
    This is a `make` alternative with a simpler syntax and some useful features.
    """
    try:
        repo_root = find_root()
        os.chdir(repo_root)

        flags = [flag.split("=", 1) + ["true"] for flag in flag]
        flags = {flag[0].lower(): loads(flag[1]) for flag in flags}

        target_rule_lookup = load_rules(flags)
        target_rule_lookup.verify()

        all_files = get_repo_files()
        source_files = target_rule_lookup.find_source_files(all_files)

        if profile:
            print("Slow Build / Rules Files (Loading Phase):")
            slowest = sorted(LOAD_TIMINGS, key=lambda x: LOAD_TIMINGS[x], reverse=True)[
                :20
            ]
            for key in slowest:
                print(key, LOAD_TIMINGS[key])

            print()

        if locate:
            if target in source_files:
                raise BuildException(
                    f"Target {target} is a source file, not a build target."
                )
            rule = target_rule_lookup.try_lookup(target)
            if rule is None and not target.startswith(":"):
                rule = target_rule_lookup.try_lookup(f":{target}")
            if rule is None:
                raise BuildException(f"Target {target} was not found.")
            print(f"Target {target} is built by {rule.name} in {rule.location}/BUILD.")
            exit(0)

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

        if profile:
            print("Slow Rules (Execution Phase):")
            slowest = sorted(
                BUILD_TIMINGS, key=lambda x: BUILD_TIMINGS[x], reverse=True
            )[:20]
            for key in slowest:
                print(key, BUILD_TIMINGS[key])

    except BuildException as e:
        display_error(e)
        exit(1)
    except Exception as e:
        display_error(BuildException("Internal error: " + repr(e)))
        print(f"\n{Style.RESET_ALL}" + traceback.format_exc())
        exit(1)


if __name__ == "__main__":
    cli()

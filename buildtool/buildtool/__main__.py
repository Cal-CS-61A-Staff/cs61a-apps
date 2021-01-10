from __future__ import annotations

import os
import traceback
from json import loads
from shutil import rmtree
from typing import List

import click
from cache import STATS
from colorama import Fore, Style

from build_coordinator import run_build
from build_worker import TIMINGS as BUILD_TIMINGS
from common.cli_utils import pretty_print
from monitoring import enable_logging, enable_profiling
from state import BuildState
from fs_utils import find_root, get_repo_files
from loader import config, load_rules, TIMINGS as LOAD_TIMINGS
from utils import BuildException
from workspace_setup import initialize_workspace


def display_error(error: BuildException):
    print(Fore.RED)
    pretty_print("🚫", "Build failed.")
    print(Style.BRIGHT)
    print(error)


@click.command()
@click.argument("target", required=False)
@click.option("--profile", "-p", default=False, is_flag=True)
@click.option("--locate", "-l", default=False, is_flag=True)
@click.option("--verbose", "-v", default=False, is_flag=True)
@click.option("--quiet", "-q", default=False, is_flag=True)
@click.option("--skip-version-check", default=False, is_flag=True)
@click.option("--skip-setup", default=False, is_flag=True)
@click.option("--skip-build", default=False, is_flag=True)
@click.option("--clean", "-c", default=False, is_flag=True)
@click.option("--threads", "-t", default=8)
@click.option("--state-directory", default=".state")
@click.option("--cache-directory", default=".cache")
@click.option("--flag", "-f", type=str, multiple=True)
def cli(
    target: str,
    profile: bool,
    locate: bool,
    verbose: bool,
    quiet: bool,
    skip_version_check: bool,
    skip_setup: bool,
    skip_build: bool,
    clean: bool,
    threads: int,
    state_directory: str,
    cache_directory: str,
    flag: List[str],
):
    """
    This is a `make` alternative with a simpler syntax and some useful features.
    """
    try:
        repo_root = find_root()
        os.chdir(repo_root)

        if verbose:
            enable_logging()

        if profile:
            enable_profiling()

        flags = [flag.split("=", 1) + ["true"] for flag in flag]
        flags = {flag[0].lower(): loads(flag[1]) for flag in flags}

        if not skip_setup:
            setup_rule_lookup = load_rules(
                flags, workspace=True, skip_version_check=skip_version_check
            )

            if target and target.startswith("setup:"):
                setup_target = target[5:]
                skip_build = True
            else:
                setup_target = config.default_setup_rule

            initialize_workspace(
                setup_rule_lookup,
                setup_target,
                state_directory,
                quiet,
            )

        target_rule_lookup = load_rules(flags, skip_version_check=skip_version_check)
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

        need_target = locate or not skip_build

        if not target and need_target:
            target = config.default_build_rule
            if target is None:
                raise BuildException("No target provided, and no default target set.")

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

        if not skip_build:
            for _ in range(2 if clean else 1):
                if clean:
                    for out_dir in config.output_directories:
                        rmtree(out_dir, ignore_errors=True)
                    for rule in set(target_rule_lookup.direct_lookup.values()) | set(
                        target_rule_lookup.direct_lookup.values()
                    ):
                        rule.pending_rule_dependencies = set()
                        rule.runtime_dependents = set()
                run_build(
                    BuildState(
                        target_rule_lookup=target_rule_lookup,
                        source_files=source_files,
                        cache_directory=cache_directory,
                        repo_root=repo_root,
                    ),
                    target,
                    threads,
                    quiet,
                )

        if profile:
            print("Slow Rules (Execution Phase):")
            slowest = sorted(
                BUILD_TIMINGS, key=lambda x: BUILD_TIMINGS[x], reverse=True
            )[:20]
            for key in slowest:
                print(key, BUILD_TIMINGS[key])
            print("Cache Statistics")
            print(
                f"{STATS['hits']} cache hits, {STATS['misses']} cache misses, {STATS['inserts']} cache inserts (approx)"
            )

    except BuildException as e:
        display_error(e)
        exit(1)
    except Exception as e:
        display_error(BuildException("Internal error: " + repr(e)))
        print(f"\n{Style.RESET_ALL}" + traceback.format_exc())
        exit(1)


if __name__ == "__main__":
    cli()

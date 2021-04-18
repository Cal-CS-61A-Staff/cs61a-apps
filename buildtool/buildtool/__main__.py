from __future__ import annotations

import os
import traceback
from json import loads
from shutil import rmtree
from typing import List, Tuple

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
@click.argument("targets", metavar="target", required=False, nargs=-1)
@click.option(
    "--profile",
    "-p",
    default=False,
    is_flag=True,
    help="Show performance profiling data, cache hit rates, and log all executed commands.",
)
@click.option(
    "--shell-log",
    "-s",
    default=False,
    is_flag=True,
    help="Log all executed commands.",
)
@click.option(
    "--locate",
    "-l",
    default=False,
    is_flag=True,
    help="Rather than building, locate the BUILD file declaring a particular target.",
)
@click.option(
    "--verbose",
    "-v",
    default=False,
    is_flag=True,
    help="Show detailed logs to identify problems. For most purposes, --profile is a better option.",
)
@click.option(
    "--quiet",
    "-q",
    default=False,
    is_flag=True,
    help="Disable the progress bars normally shown during a build. Does not affect the output of "
    "--locate or --profile, and errors will still be printed if the build fails.",
)
@click.option(
    "--skip-version-check",
    default=False,
    is_flag=True,
    help="Ignore any minimum version requirements specified in the WORKSPACE file.",
)
@click.option(
    "--skip-setup",
    default=False,
    is_flag=True,
    help="Do not install / verify dependencies in the WORKSPACE file.",
)
@click.option(
    "--skip-build",
    default=False,
    is_flag=True,
    help="Do not build the targets passed in. Automatically set when running --locate.",
)
@click.option(
    "--clean",
    "-c",
    default=False,
    is_flag=True,
    help="Clean the output directory specified in the WORKSPACE file so only built targets will be kept.",
)
@click.option(
    "--threads",
    "-t",
    "num_threads",
    default=8,
    help="The number of worker threads used in execution. Increase this number if using a remote build cache.",
)
@click.option(
    "--state-directory",
    default=".state",
    help="The local directory used to keep track of the state of the WORKSPACE install.",
)
@click.option(
    "--cache-directory",
    default=os.getenv("BUILDTOOL_CACHE_DIRECTORY", ".cache"),
    help="The directory used to cache build outputs and intermediate layers. If a cloud storage bucket is passed "
    "in as gs://bucket-name, it will be used alongside an .aux_cache local directory as a source for cached outputs. "
    "Override with the BUILDTOOL_CACHE_DIRECTORY environment variable.",
)
@click.option(
    "--flag",
    "-f",
    "flags",
    type=str,
    multiple=True,
    help="These flags are exposed at load and build time, via `from buildtool import flags`. "
    "Values can be supplied as JSON like --flag KEY=JSON_VALUE, and flags without values default to `true`.",
)
def cli(
    targets: Tuple[str],
    profile: bool,
    shell_log: bool,
    locate: bool,
    verbose: bool,
    quiet: bool,
    skip_version_check: bool,
    skip_setup: bool,
    skip_build: bool,
    clean: bool,
    num_threads: int,
    state_directory: str,
    cache_directory: str,
    flags: List[str],
):
    """
    This is a `make` alternative with a simpler syntax and some useful features.
    """
    try:
        repo_root = find_root()
        os.chdir(repo_root)

        if verbose:
            enable_logging()

        if profile or shell_log:
            enable_profiling()

        flags = [flag.split("=", 1) + ["true"] for flag in flags]
        flags = {flag[0].lower(): loads(flag[1]) for flag in flags}

        if not skip_setup:
            setup_rule_lookup = load_rules(
                flags, workspace=True, skip_version_check=skip_version_check
            )

            setup_targets = [
                target[5:] for target in targets if target.startswith("setup:")
            ]

            if locate and setup_targets:
                raise BuildException(
                    "--locate cannot be used with setup rules - they are declared in WORKSPACE"
                )

            setup_targets = setup_targets or (
                [config.default_setup_rule] if config.default_setup_rule else []
            )

            initialize_workspace(
                setup_rule_lookup,
                setup_targets,
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

        if not targets and need_target:
            if config.default_build_rule is None:
                raise BuildException("No target provided, and no default target set.")
            targets = [config.default_build_rule]

        if locate:
            for target in targets:
                if target in source_files:
                    raise BuildException(
                        f"Target {target} is a source file, not a build target."
                    )
                rule = target_rule_lookup.try_lookup(target)
                if rule is None and not target.startswith(":"):
                    rule = target_rule_lookup.try_lookup(f":{target}")
                if rule is None:
                    raise BuildException(f"Target {target} was not found.")
                print(
                    f"Target {target} is declared by {rule} in {rule.location}/BUILD."
                )
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
                    [target for target in targets if not target.startswith("setup:")],
                    num_threads,
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

import os

import click
from analysis import generate_runtime_rules
from execution import execute_build
from fs_utils import find_root
from loader import load_rules
from planning import find_needed_rules
from utils import BuildException


@click.command()
@click.argument("target")
@click.option("--threads", "-t", default=4)
@click.option("--cache-directory", default=".cache")
def cli(target: str, threads: int, cache_directory: str):
    """
    This is a `make` alternative with a simpler syntax and some useful features.
    """
    repo_root = find_root()
    os.chdir(repo_root)

    target_rule_lookup = load_rules()

    target_runtime_rule_lookup = generate_runtime_rules(target_rule_lookup)

    if target not in target_rule_lookup:
        raise BuildException(f"Target `{target} not found in BUILD files.")
    target_runtime_rule = target_runtime_rule_lookup[target]

    needed, start_rules = find_needed_rules(target_runtime_rule)

    execute_build(start_rules, needed, threads, cache_directory)


if __name__ == "__main__":
    cli()

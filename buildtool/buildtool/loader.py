from __future__ import annotations

import os
import sys
from glob import glob
from typing import Callable, Optional, Sequence, Union

from state import Rule, TargetLookup
from utils import BuildException
from fs_utils import find_root, get_repo_files, normalize_path


def make_callback(
    repo_root: str,
    build_root: str,
    # output parameter
    target_rule_lookup: TargetLookup,
):
    def fail(target):
        raise BuildException(
            f"The target `{target}` is built by multiple rules. Targets can only be produced by a single rule."
        )

    def add_target_rule(target, rule):
        if target.endswith("/"):
            # it's a folder dependency
            if target in target_rule_lookup.location_lookup:
                fail(target)
            target_rule_lookup.location_lookup[target] = rule
        else:
            if target in target_rule_lookup.direct_lookup:
                fail(target)
            target_rule_lookup.direct_lookup[target] = rule

    def callback(
        *,
        name: Optional[str] = None,
        deps: Sequence[str] = (),
        impl: Callable,
        out: Union[str, Sequence[str]] = (),
    ):
        if isinstance(out, str):
            out = [out]
        rule = Rule(
            name=name,
            location=build_root,
            deps=[
                dep
                if dep.startswith(":")
                else normalize_path(repo_root, build_root, dep)
                for dep in deps
            ],
            impl=impl,
            outputs=[normalize_path(repo_root, build_root, output) for output in out],
        )
        for output in rule.outputs:
            add_target_rule(output, rule)

        if name is not None:
            add_target_rule(":" + name, rule)

    def find(path):
        return [
            os.path.relpath(path, build_root)
            for path in glob(
                normalize_path(repo_root, build_root, path),
                recursive=True,
            )
        ]

    return callback, find


class Struct:
    def __init__(self, entries):
        self.__dict__.update(entries)


def make_load_rules(repo_root: str, rules_root: str):
    def load_rules(path):
        path = normalize_path(repo_root, rules_root, path)
        if not path.endswith(".py"):
            raise BuildException(f"Cannot import from a non .py file: {path}")

        __builtins__["load"] = make_load_rules(repo_root, path)
        cached_callback = __builtins__["callback"]
        cached_find = __builtins__["find"]
        del __builtins__["callback"]
        del __builtins__["find"]
        # We hide the callback here, since you should not be running the
        # callback (or anything else!) in an import, but just providing defs
        frame = {"__builtins__": __builtins__}
        reset_mock_imports(frame, ["load"])
        with open(path) as f:
            exec(f.read(), frame)
        __builtins__["callback"] = cached_callback
        __builtins__["find"] = cached_find
        return Struct(frame)

    return load_rules


def reset_mock_imports(frame, targets):
    exec(
        "import buildtool; "
        + " ".join(f"buildtool.{target} = {target};" for target in targets),
        frame,
    )


def load_rules():
    repo_root = find_root()
    src_files = get_repo_files()
    build_files = [file for file in src_files if file.split("/")[-1] == "BUILD"]
    target_rule_lookup = TargetLookup()
    frame = {}
    sys.path.insert(0, repo_root)
    for build_file in build_files:
        with open(build_file) as f:
            callback, find = make_callback(
                repo_root, os.path.dirname(build_file), target_rule_lookup
            )
            load = make_load_rules(repo_root, os.path.dirname(build_file))

            __builtins__["callback"] = callback
            __builtins__["find"] = find
            __builtins__["load"] = load

            frame = {
                **frame,
                "__builtins__": __builtins__,
            }

            reset_mock_imports(frame, ["callback", "find", "load"])

            exec(f.read(), frame)
    return target_rule_lookup

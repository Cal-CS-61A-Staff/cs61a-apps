from __future__ import annotations

import os
import sys
import time
import traceback
from glob import glob
from typing import Callable, Dict, Optional, Sequence, Union

from colorama import Style

from fs_utils import find_root, get_repo_files, normalize_path
from state import Rule, TargetLookup
from utils import BuildException

LOAD_FRAME_CACHE: Dict[str, Struct] = {}

TIMINGS = {}

start_time_stack = []


def make_callback(
    repo_root: str,
    build_root: Optional[str],
    # output parameter
    target_rule_lookup: TargetLookup,
):
    make_callback.build_root = build_root
    make_callback.find_cache = {}

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
        build_root = make_callback.build_root

        if build_root is None:
            raise BuildException(
                "Rules files can only define functions, not invoke callback()"
            )

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
        build_root = make_callback.build_root

        target = normalize_path(repo_root, build_root, path)

        if target in make_callback.find_cache:
            return make_callback.find_cache[target]

        if build_root is None:
            raise BuildException(
                "Rules files can only define functions, not invoke find()"
            )

        make_callback.find_cache[target] = out = [
            "//" + os.path.relpath(path, repo_root)
            for path in glob(
                normalize_path(repo_root, build_root, path),
                recursive=True,
            )
        ]

        return out

    return callback, find


class Struct:
    def __init__(self, entries, default=False):
        self.__dict__.update(entries)
        self.default = default

    def __getattr__(self, item):
        if self.default:
            return None
        else:
            return getattr(super(), item)


def make_load_rules(repo_root: str, rules_root: str):
    rules_root = os.path.dirname(rules_root)

    def load_rules(path):
        path = normalize_path(repo_root, rules_root, path)
        if not path.endswith(".py"):
            raise BuildException(f"Cannot import from a non .py file: {path}")

        if path in LOAD_FRAME_CACHE:
            return LOAD_FRAME_CACHE[path]

        start_time_stack.append(time.time())

        __builtins__["load"] = make_load_rules(repo_root, path)
        # We hide the callback here, since you should not be running the
        # callback (or anything else!) in an import, but just providing defs
        frame = {"__builtins__": __builtins__}
        reset_mock_imports(frame, ["load"])
        cached_root = make_callback.build_root
        make_callback.build_root = None
        with open(path) as f:
            try:
                exec(f.read(), frame)
            except Exception:
                raise BuildException(
                    f"Error while processing rules file {path}:\n"
                    + f"\n{Style.RESET_ALL}"
                    + traceback.format_exc()
                )
        make_callback.build_root = cached_root

        TIMINGS[path] = load_time = time.time() - start_time_stack.pop()
        start_time_stack[0] += load_time

        out = LOAD_FRAME_CACHE[path] = Struct(frame)
        return out

    return load_rules


def reset_mock_imports(frame, targets):
    exec(
        "import buildtool; "
        + " ".join(f"buildtool.{target} = {target};" for target in targets),
        frame,
    )


def load_rules(flags: Dict[str, object]):
    flags = Struct(flags, default=True)
    repo_root = find_root()
    src_files = get_repo_files()
    build_files = [file for file in src_files if file.split("/")[-1] == "BUILD"]
    target_rule_lookup = TargetLookup()
    sys.path.insert(0, repo_root)
    callback, find = make_callback(repo_root, None, target_rule_lookup)
    for build_file in build_files:
        make_callback.build_root = os.path.dirname(build_file)

        with open(build_file) as f:
            frame = {}
            load = make_load_rules(repo_root, os.path.dirname(build_file))

            __builtins__["callback"] = callback
            __builtins__["find"] = find
            __builtins__["load"] = load
            __builtins__["flags"] = flags

            frame = {
                **frame,
                "__builtins__": __builtins__,
            }

            reset_mock_imports(frame, ["callback", "find", "load", "flags"])
            start_time_stack.append(time.time())
            try:
                exec(f.read(), frame)
            except BuildException:
                raise
            except Exception:
                raise BuildException(
                    f"Error while processing BUILD file {build_file}:\n"
                    + f"\n{Style.RESET_ALL}"
                    + traceback.format_exc()
                )
            TIMINGS[build_file] = time.time() - start_time_stack.pop()
    return target_rule_lookup

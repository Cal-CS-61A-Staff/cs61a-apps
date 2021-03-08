from __future__ import annotations

import os
import sys
import time
import traceback
from dataclasses import dataclass, field
from glob import glob
from importlib.metadata import version
from typing import Callable, Dict, List, Optional, Sequence, Set, Union

from colorama import Style

from fs_utils import find_root, get_repo_files, normalize_path
from packaging.version import parse
from state import Rule, TargetLookup
from utils import BuildException

LOAD_FRAME_CACHE: Dict[str, Struct] = {}

TIMINGS = {}

start_time_stack = []


@dataclass
class Config:
    # CLI config
    skip_version_check: bool = False

    # loaded config
    default_setup_rule: Optional[str] = None
    default_build_rule: Optional[str] = None
    active: bool = False
    output_directories: List[str] = field(default_factory=list)

    def _check_active(self):
        if not self.active:
            raise BuildException("Cannot use config in this context.")

    @staticmethod
    def _check_rule(rule: str):
        if not rule.startswith(":"):
            raise BuildException(f"Can only register a rule, not {rule}")

    def register_default_setup_rule(self, rule: str):
        self._check_active()
        self._check_rule(rule)
        if self.default_setup_rule is not None:
            raise BuildException(
                f"Default setup rule is already set to {self.default_setup_rule}"
            )
        self.default_setup_rule = rule

    def register_default_build_rule(self, rule: str):
        self._check_active()
        self._check_rule(rule)
        if self.default_build_rule is not None:
            raise BuildException(
                f"Default build rule is already set to {self.default_build_rule}"
            )
        self.default_build_rule = rule

    def register_output_directory(self, path: str):
        self._check_active()
        self.output_directories.append(normalize_path(os.curdir, os.curdir, path))

    def require_buildtool_version(self, min_version: str):
        if self.skip_version_check:
            return
        curr_version = version("buildtool").replace("-", "9999")
        if parse(curr_version) < parse(min_version):
            raise BuildException(
                f"Current buildtool version {curr_version} < {min_version}, the minimum required "
                "for this project. Please upgrade, or pass in --skip-version-check to skip this check."
            )


config = Config()


def make_callback(
    repo_root: str,
    build_root: Optional[str],
    src_files: Set[str],
    # output parameter
    target_rule_lookup: TargetLookup,
):
    make_callback.build_root = build_root
    make_callback.find_cache = {}
    make_callback.target_rule_lookup = target_rule_lookup

    def fail(target):
        raise BuildException(
            f"The target `{target}` is built by multiple rules. Targets can only be produced by a single rule."
        )

    def add_target_rule(target, rule):
        target_rule_lookup = make_callback.target_rule_lookup
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
        impl: Callable = lambda _: None,
        out: Union[str, Sequence[str]] = (),
        do_not_symlink: bool = False,
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
            do_not_symlink=do_not_symlink,
        )
        for output in rule.outputs:
            add_target_rule(output, rule)

        if name is not None:
            add_target_rule(":" + name, rule)

        return f":{name}"

    def find(path, *, unsafe_ignore_extension=False):
        build_root = make_callback.build_root

        target = normalize_path(repo_root, build_root, path)

        if target in make_callback.find_cache:
            return make_callback.find_cache[target]

        if build_root is None:
            raise BuildException(
                "Rules files can only define functions, not invoke find()"
            )

        if not unsafe_ignore_extension:
            ext = path.split(".")[-1]
            if "/" in ext:
                raise BuildException(
                    "Cannot find() files without specifying an extension"
                )

        out = [
            os.path.relpath(path, repo_root)
            for path in glob(
                normalize_path(repo_root, build_root, path),
                recursive=True,
            )
        ]

        make_callback.find_cache[target] = out = [
            "//" + path
            for path in out
            if os.path.relpath(os.path.realpath(path), repo_root) in src_files
        ]

        return sorted(out)

    def resolve(path):
        build_root = make_callback.build_root

        if build_root is None:
            raise BuildException(
                "Rules files can only define functions, not invoke resolve(). "
                "If you are in an impl() function, use ctx.resolve() instead."
            )

        return "//" + normalize_path(repo_root, build_root, path)

    return callback, find, resolve


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
    make_load_rules.rules_root = os.path.dirname(rules_root)

    def load_rules(path):
        path = normalize_path(repo_root, make_load_rules.rules_root, path)
        if not path.endswith(".py"):
            raise BuildException(f"Cannot import from a non .py file: {path}")

        if path in LOAD_FRAME_CACHE:
            return LOAD_FRAME_CACHE[path]

        start_time_stack.append(time.time())

        old_rules_root = make_load_rules.rules_root
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
        make_load_rules.rules_root = old_rules_root

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


def load_rules(
    flags: Dict[str, object],
    *,
    skip_version_check: bool,
    workspace: bool = False,
):
    flags = Struct(flags, default=True)
    repo_root = find_root()
    src_files = get_repo_files()
    build_files = (
        ["WORKSPACE"]
        if workspace
        else [file for file in src_files if file.split("/")[-1] == "BUILD"]
    )
    target_rule_lookup = TargetLookup()
    sys.path.insert(0, repo_root)
    callback, find, resolve = make_callback(
        repo_root, None, set(src_files), target_rule_lookup
    )
    config.skip_version_check = skip_version_check
    for build_file in build_files:
        make_callback.build_root = os.path.dirname(build_file)

        with open(build_file) as f:
            frame = {}
            load = make_load_rules(repo_root, build_file)

            __builtins__["callback"] = callback
            __builtins__["find"] = find
            __builtins__["resolve"] = resolve
            __builtins__["load"] = load
            __builtins__["flags"] = flags

            frame = {
                **frame,
                "__builtins__": __builtins__,
            }

            reset_mock_imports(frame, ["callback", "find", "load", "flags", "resolve"])

            if workspace:
                __builtins__["config"] = config
                config.active = True
                reset_mock_imports(frame, ["config"])

            start_time_stack.append(time.time())
            try:
                exec(f.read(), frame)
                config.active = False
            except Exception:
                raise BuildException(
                    f"Error while processing BUILD file {build_file}:\n"
                    + f"\n{Style.RESET_ALL}"
                    + traceback.format_exc()
                )
            TIMINGS[build_file] = time.time() - start_time_stack.pop()

        make_callback.build_root = None

    return target_rule_lookup

import os
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Sequence, Union

from utils import BuildException
from fs_utils import find_root, get_repo_files, normalize_path


@dataclass(eq=False)
class LoadedRule:
    name: Optional[str]
    location: str
    deps: Sequence[str]
    impl: Callable
    outputs: Sequence[str]

    def __hash__(self):
        return id(self)

    def __str__(self):
        if self.name:
            return self.name
        elif len(self.outputs) == 1:
            return self.outputs[0]
        else:
            return f"<anonymous rule from {self.location}/BUILD>"


def make_callback(
    repo_root: str,
    build_root: str,
    # output parameter
    target_rule_lookup: Dict[str, LoadedRule],
):
    def add_target_rule(target, rule):
        if target in target_rule_lookup:
            raise BuildException(
                f"The target `{target}` is built by multiple rules. Targets can only be produced by a single rule."
            )
        target_rule_lookup[target] = rule

    def callback(
        *,
        name: Optional[str] = None,
        deps: Sequence[str] = (),
        impl: Callable,
        outputs: Union[str, Sequence[str]] = (),
    ):
        if isinstance(outputs, str):
            outputs = [outputs]
        rule = LoadedRule(
            name=name,
            location=build_root,
            deps=[normalize_path(repo_root, build_root, dep) for dep in deps],
            impl=impl,
            outputs=[
                normalize_path(repo_root, build_root, output) for output in outputs
            ],
        )
        for output in outputs:
            add_target_rule(normalize_path(repo_root, build_root, output), rule)

        if name is not None:
            add_target_rule(name, rule)

    return callback


def load_rules():
    repo_root = find_root()
    src_files = get_repo_files()
    build_files = [file for file in src_files if file.split("/")[-1] == "BUILD"]
    target_rule_lookup: Dict[str, LoadedRule] = {}
    frame = {}
    for build_file in build_files:
        with open(build_file) as f:
            callback = make_callback(
                repo_root, os.path.dirname(build_file), target_rule_lookup
            )
            frame = {**frame, "callback": callback}
            exec("import rules; rules.callback = callback", frame)
            exec(f.read(), frame)
    return target_rule_lookup

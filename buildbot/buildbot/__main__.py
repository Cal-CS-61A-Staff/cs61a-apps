from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
import os
from pathlib import Path
from queue import SimpleQueue
from typing import Callable, Dict, List, Optional, Sequence, Union

import click

from common.shell_utils import sh


@dataclass
class SourceFile:
    path: str  # relative to repo_root


class Context(ABC):
    def sh(self, cmd: str):
        raise NotImplemented


class PreviewContext(Context):
    def sh(self, cmd: str):
        return cmd


class ExecutionContext(Context):
    def __init__(self, cwd: str):
        self.cwd = cwd

    def sh(self, cmd: str):
        sh(cmd, shell=True, cwd=self.cwd)


@dataclass(eq=False)
class PreparingAction:
    name: Optional[str]
    location: str
    deps: Sequence[str]
    action: Callable
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


@dataclass(eq=False)
class RuntimeAction:
    # scheduling fields
    dependencies: List[Union[RuntimeAction, SourceFile]]
    remaining_action_dependencies: List[RuntimeAction]
    dependents: List[RuntimeAction]  # includes dependents that are not actually needed

    # execution fields
    action: Callable
    inputs: Sequence[str]
    outputs: Sequence[str]
    working_directory: str

    # debugging
    name: str

    def __hash__(self):
        return hash(id(self))

    def __str__(self):
        return self.name


class BuildException(Exception):
    pass


def get_repo_files():
    return [
        file.decode("ascii") if isinstance(file, bytes) else file
        for file in sh(
            "git", "ls-files", "--exclude-standard", capture_output=True, quiet=True
        ).splitlines()  # All tracked files
        + sh(
            "git",
            "ls-files",
            "-o",
            "--exclude-standard",
            capture_output=True,
            quiet=True,
        ).splitlines()  # Untracked but not ignored files
    ]


def normalize_path(repo_root, build_root, path):
    if path.startswith("//"):
        path = os.path.join(repo_root, path[2:])
    else:
        path = os.path.join(build_root, path)
    path = Path(path)
    repo_root = Path(repo_root)
    if repo_root not in path.parents:
        raise BuildException(
            f"Target `{path}` is not in the root directory of the repo."
        )
    return str(path.relative_to(repo_root))


def make_callback(
    repo_root: str,
    build_root: str,
    # output parameter
    target_action_lookup: Dict[str, PreparingAction],
):
    def add_target_action(target, action):
        if target in target_action_lookup:
            raise BuildException(
                f"The target `{target}` is built by multiple actions. Targets can only be produced by a single action."
            )
        target_action_lookup[target] = action

    def callback(
        *,
        name: Optional[str] = None,
        deps: Sequence[str] = (),
        action: Callable,
        outputs: Union[str, Sequence[str]] = (),
    ):
        if isinstance(outputs, str):
            outputs = [outputs]
        action = PreparingAction(
            name,
            build_root,
            [normalize_path(repo_root, build_root, dep) for dep in deps],
            action,
            outputs,
        )
        for output in outputs:
            add_target_action(normalize_path(repo_root, build_root, output), action)

        if name is not None:
            add_target_action(name, action)

    return callback


@click.command()
@click.argument("target")
def cli(target):
    """
    This is a `make` alternative with a simpler syntax and some useful features.
    """

    # loading phase
    repo_root = "."  # fixme look for a WORKSPACE file

    src_files = get_repo_files()
    build_files = [file for file in src_files if file.split("/")[-1] == "BUILD"]

    target_action_lookup: Dict[str, PreparingAction] = {}

    frame = {}

    for build_file in build_files:
        with open(build_file) as f:
            callback = make_callback(
                repo_root, os.path.dirname(build_file), target_action_lookup
            )
            frame = {**frame, "callback": callback}
            exec("import rules; rules.callback = callback", frame)
            exec(f.read(), frame)

    # analysis phase
    preparing_to_runtime_action_lookup = {}
    for action in set(target_action_lookup.values()):
        preparing_to_runtime_action_lookup[action] = RuntimeAction(
            [], [], [], action.action, [], action.outputs, action.location, str(action)
        )

    for preparing_action, runtime_action in preparing_to_runtime_action_lookup.items():
        dependencies = []
        action_dependencies = []
        inputs = []
        for dependency in preparing_action.deps:
            inputs.append(dependency)
            if dependency in target_action_lookup:
                # it is a generated file
                runtime_dependency = preparing_to_runtime_action_lookup[
                    target_action_lookup[dependency]
                ]
                dependencies.append(runtime_action)
                runtime_dependency.dependents.append(runtime_action)
                action_dependencies.append(runtime_dependency)
            elif dependency in src_files:
                # it is a file within the repo
                dependencies.append(SourceFile(dependency))
            else:
                raise BuildException(
                    f"Dependency `{dependency}` is not valid as it is neither a source file nor the output of another "
                    f"rule. "
                )
        runtime_action.remaining_action_dependencies = action_dependencies
        runtime_action.dependencies = dependencies
        runtime_action.inputs = inputs

    # pre-execution phase
    if target not in target_action_lookup:
        raise BuildException(f"Target `{target} not found in BUILD files.")

    needed = set()
    start_actions = set()

    def find_dependencies(action: RuntimeAction, dependents: List[RuntimeAction]):
        if action in dependents:
            dependents.append(action)
            raise BuildException(
                f"Circular dependency detected: {action} depends on itself "
                f"through the path: {' -> '.join(map(str, dependents))}"
            )
        dependents.append(action)
        for dep in action.remaining_action_dependencies:
            find_dependencies(dep, dependents)
        dependents.pop()
        needed.add(action)
        if not action.remaining_action_dependencies:
            start_actions.add(action)

    find_dependencies(
        preparing_to_runtime_action_lookup[target_action_lookup[target]], []
    )

    # execution phase
    work_queue: SimpleQueue[RuntimeAction] = SimpleQueue()
    for action in start_actions:
        work_queue.put(action)

    while True:
        # fixme: does not terminate!
        todo = work_queue.get()
        context = ExecutionContext(todo.working_directory)
        todo.action(context)
        for dependent in todo.dependents:
            dependent.remaining_action_dependencies.remove(todo)
            if not dependent.remaining_action_dependencies:
                work_queue.put(dependent)


if __name__ == "__main__":
    cli()

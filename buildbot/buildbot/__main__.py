from __future__ import annotations

import hashlib
from abc import ABC
from dataclasses import dataclass
import os
from pathlib import Path
from queue import Queue
from shutil import SameFileError, copyfile, rmtree
from threading import Lock, Thread
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
    def __init__(self):
        self.log = []

    def sh(self, cmd: str):
        self.log.append(cmd.encode("utf-8"))


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

    # synchronization
    lock: Lock

    # debugging
    name: str

    def __hash__(self):
        return hash(id(self))

    def __str__(self):
        return self.name


class BuildException(Exception):
    pass


def find_root():
    repo_root = os.path.abspath(os.path.curdir)
    while True:
        if "WORKSPACE" in os.listdir(repo_root):
            return repo_root
        repo_root = os.path.dirname(repo_root)
        if repo_root == os.path.dirname(repo_root):
            break
    raise BuildException(
        "Unable to find WORKSPACE file - are you in the project directory?"
    )


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
    path = Path(path).absolute()
    repo_root = Path(repo_root).absolute()
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
            name=name,
            location=build_root,
            deps=[normalize_path(repo_root, build_root, dep) for dep in deps],
            action=action,
            outputs=[
                normalize_path(repo_root, build_root, output) for output in outputs
            ],
        )
        for output in outputs:
            add_target_action(normalize_path(repo_root, build_root, output), action)

        if name is not None:
            add_target_action(name, action)

    return callback


def copy_helper(*, src_root, dest_root, src_names, dest_names=None, symlink=False):
    if not dest_names:
        dest_names = src_names
    assert len(src_names) == len(dest_names)
    for src_name, dest_name in zip(src_names, dest_names):
        src = Path(src_root).joinpath(src_name)
        dest = Path(dest_root).joinpath(dest_name)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        try:
            if symlink:
                Path(dest).symlink_to(src)
            else:
                copyfile(src, dest)
        except SameFileError:
            pass


@click.command()
@click.argument("target")
@click.option("--threads", "-t", default=4)
@click.option("--cache-directory", default=".cache")
def cli(target: str, threads: int, cache_directory: str):
    """
    This is a `make` alternative with a simpler syntax and some useful features.
    """

    # loading phase
    repo_root = find_root()
    os.chdir(repo_root)

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
            name=str(action),
            action=action.action,
            outputs=action.outputs,
            working_directory=action.location,
            lock=Lock(),
            # to be filled in later
            dependencies=[],
            remaining_action_dependencies=[],
            dependents=[],
            inputs=[],
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

    target_runtime_action = preparing_to_runtime_action_lookup[
        target_action_lookup[target]
    ]

    find_dependencies(target_runtime_action, [])

    # execution phase
    work_queue: Queue[Optional[RuntimeAction]] = Queue()
    for action in start_actions:
        work_queue.put(action)

    def worker(index: int):
        scratch_path = Path(repo_root).joinpath(Path(f".scratch_{index}"))
        if scratch_path.exists():
            rmtree(scratch_path)
        while True:
            todo = work_queue.get()
            if todo is None:
                return
            # first check if it's cached
            preview_context = PreviewContext()
            todo.action(preview_context)
            m = hashlib.md5()
            for log in preview_context.log:
                m.update(log)
            for input_path in todo.inputs:
                m.update(input_path.encode("utf-8"))
                with open(input_path, "rb") as f:
                    m.update(f.read())
            for output_path in todo.outputs:
                m.update(output_path.encode("utf-8"))
            key = m.hexdigest()
            cache_location = Path(cache_directory).joinpath(key)
            cache_output_names = [
                hashlib.md5(output_path.encode("utf-8")).hexdigest()
                for output_path in todo.outputs
            ]
            if cache_location.exists():
                try:
                    copy_helper(
                        src_root=cache_location,
                        src_names=cache_output_names,
                        dest_root=repo_root,
                        dest_names=todo.outputs,
                    )
                except FileNotFoundError:
                    raise BuildException(
                        "Cache corrupted. This should never happen unless you modified the cache directory manually!"
                    )
            else:
                scratch_path.mkdir(exist_ok=True)
                copy_helper(
                    src_root=repo_root,
                    src_names=todo.inputs,
                    dest_root=scratch_path,
                    symlink=True,
                )
                todo.action(
                    ExecutionContext(scratch_path.joinpath(todo.working_directory))
                )
                try:
                    copy_helper(
                        src_root=scratch_path,
                        src_names=todo.outputs,
                        dest_root=repo_root,
                    )
                except FileNotFoundError as e:
                    raise BuildException(
                        f"Output file {e.filename} from rule {todo} was not generated."
                    )
                copy_helper(
                    src_root=scratch_path,
                    src_names=todo.outputs,
                    dest_root=cache_location,
                    dest_names=cache_output_names,
                )
                rmtree(scratch_path)

            for dependent in todo.dependents:
                if dependent in needed:
                    dependent.lock.acquire()
                    dependent.remaining_action_dependencies.remove(todo)
                    if not dependent.remaining_action_dependencies:
                        work_queue.put(dependent)
                    dependent.lock.release()
            work_queue.task_done()

    thread_instances = []
    for i in range(threads):
        thread = Thread(target=worker, args=(i,))
        thread_instances.append(thread)
        thread.start()

    work_queue.join()

    for _ in range(threads):
        work_queue.put(None)

    for thread in thread_instances:
        thread.join()


if __name__ == "__main__":
    cli()

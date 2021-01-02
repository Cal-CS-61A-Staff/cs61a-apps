from __future__ import annotations

import hashlib
from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from queue import Queue
from shutil import rmtree
from threading import Lock, Thread
from typing import Callable, List, Optional, Sequence, Set

from utils import BuildException
from fs_utils import copy_helper, find_root

from common.shell_utils import sh


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
class RuntimeRule:
    # scheduling fields
    remaining_rule_dependencies: List[RuntimeRule]
    dependents: List[RuntimeRule]  # includes dependents that are not actually needed

    # execution fields
    impl: Callable
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


def execute_build(
    start_rules: Set[RuntimeRule],
    needed: Set[RuntimeRule],
    num_threads,
    cache_directory: str,
):
    repo_root = find_root()

    work_queue: Queue[Optional[RuntimeRule]] = Queue()
    for rule in start_rules:
        work_queue.put(rule)

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
            todo.impl(preview_context)
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
                todo.impl(
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
                    dependent.remaining_rule_dependencies.remove(todo)
                    if not dependent.remaining_rule_dependencies:
                        work_queue.put(dependent)
                    dependent.lock.release()
            work_queue.task_done()

    thread_instances = []
    for i in range(num_threads):
        thread = Thread(target=worker, args=(i,))
        thread_instances.append(thread)
        thread.start()
    work_queue.join()
    for _ in range(num_threads):
        work_queue.put(None)
    for thread in thread_instances:
        thread.join()

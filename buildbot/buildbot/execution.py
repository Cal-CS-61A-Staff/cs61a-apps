from __future__ import annotations

import hashlib
from abc import ABC
from dataclasses import dataclass
from pathlib import Path
from queue import Queue
from shutil import rmtree
from threading import Thread
from typing import Callable, List, Optional, Sequence, Set

from fs_utils import copy_helper, find_root, normalize_path
from loader import Rule
from utils import BuildException, HashState

from common.shell_utils import sh as run_shell


class Context(ABC):
    def __init__(self, repo_root: str, cwd: str):
        self.repo_root = repo_root
        self.cwd = cwd

    def resolve(self, path: str):
        return normalize_path(self.repo_root, self.cwd, path)

    def sh(self, cmd: str):
        raise NotImplementedError

    def add_dep(self, dep: str):
        self.add_deps([dep])

    def add_deps(self, deps: Sequence[str]):
        raise NotImplementedError

    def input(self, *, file: str, sh: str):
        raise NotImplementedError


class MemorizeContext(Context):
    def __init__(self, repo_root: str, cwd: str, hashstate: HashState):
        super().__init__(repo_root, cwd)
        self.hashstate = hashstate

    def sh(self, cmd: str):
        self.hashstate.record("sh", cmd)

    def add_deps(self, deps: Sequence[str]):
        pass

    def input(self, *, file: str, sh: str):
        pass


class PreviewContext(MemorizeContext):
    def __init__(
        self,
        repo_root: str,
        cwd: str,
        hashstate: HashState,
        dep_fetcher: Callable[[str], str],
        cache_fetcher: Callable[[str, str], str],
    ):
        super().__init__(repo_root, cwd, hashstate)

        self.inputs = []
        self.outputs = []
        self.dep_fetcher = dep_fetcher
        self.cache_fetcher = cache_fetcher

    def add_deps(self, deps: List[str]):
        super().add_deps(deps)
        for dep in deps:
            self.inputs.append(normalize_path(self.repo_root, self.cwd, dep))

    def input(self, *, file: str = None, sh: str = None):
        super().input(file=file, sh=sh)
        if file is not None:
            self.inputs.append(normalize_path(self.repo_root, self.cwd, file))
        else:
            return self.cache_fetcher(
                self.hashstate.state(),
                hashlib.md5(sh.encode("utf-8")).hexdigest(),
            )


class ExecutionContext(MemorizeContext):
    def __init__(
        self,
        repo_root: str,
        cwd: str,
        hashstate: HashState,
        load_deps: Callable[[Sequence[str]], None],
        memorize: Callable[[str, str, str], None],
    ):
        super().__init__(repo_root, cwd, hashstate)
        self.load_deps = load_deps
        self.memorize = memorize

    def sh(self, cmd: str):
        super().sh(cmd)
        run_shell(cmd, shell=True, cwd=self.cwd)

    def add_deps(self, deps: Sequence[str]):
        super().add_deps(deps)
        self.load_deps(deps)

    def input(self, *, file: str, sh: str):
        super().input(file=file, sh=sh)
        if file is not None:
            self.add_dep(file)
            with open(normalize_path(self.repo_root, self.cwd, file), "r") as f:
                return f.read()
        else:
            out = run_shell(sh, shell=True, cwd=self.cwd, capture_output=True)
            self.memorize(
                self.hashstate.state(), hashlib.md5(sh.encode("utf-8")).hexdigest(), out
            )
            return out


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
            preview_context = PreviewContext(
                repo_root, todo.rule.location, dep_fetcher, cache_directory
            )
            todo.impl(preview_context)
            m = hashlib.md5()
            for log in preview_context.log:
                m.update(log)
            for input_path in list(todo.inputs) + preview_context.inputs:
                m.update(input_path.encode("utf-8"))
                with open(input_path, "rb") as f:
                    m.update(f.read())
            for output_path in list(todo.outputs) + preview_context.outputs:
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
                    ExecutionContext(
                        scratch_path, scratch_path.joinpath(todo.working_directory)
                    )
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
                    dependent.pending_rule_dependencies.remove(todo)
                    if not dependent.pending_rule_dependencies:
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

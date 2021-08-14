from __future__ import annotations

import inspect
import os
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from os import mkdir
from subprocess import CalledProcessError
from typing import Dict, List, Optional, Sequence, Tuple, TypeVar, Union

from common.shell_utils import sh, tmp_directory


@dataclass(frozen=True)
class File:
    path: str


class Action(ABC):
    @abstractmethod
    def to_statements(self, env: Environment) -> List[str]:
        raise NotImplemented


def indent_action_list(
    actions: List[Action], env: Environment, indent=" " * 4
) -> List[str]:
    if not actions:
        return [indent + "pass"]
    return [
        indent + statement
        for action in actions
        for statement in action.to_statements(env)
    ]


@dataclass
class Rule:
    name: str
    steps: List[Action]
    output: File

    def to_declaration(self, env: Environment) -> str:
        env.current_rule = self
        try:
            impl = f"{self.name}_impl"
            impl_contents = "\n".join(
                [f"def {impl}(ctx):", *indent_action_list(self.steps, env)]
            )
        finally:
            env.current_rule = None
        return f'{impl_contents}\n\ncallback(name="{self.name}", impl={impl}, out="{self.output.path}")'


@dataclass
class AddDep(Action):
    dep: Union[File, Rule]

    def to_statements(self, env: Environment) -> List[str]:
        if isinstance(self.dep, File):
            return [f"ctx.add_dep('{self.dep.path}')"]
        elif isinstance(self.dep, Rule):
            return [f"ctx.add_dep(':{self.dep.name}')"]


T = TypeVar("T")


class ActionWithInputs(Action, ABC):
    cached: Dict[Sequence[Tuple[File, int]], T]
    inputs: List[File]
    latest: T
    data: object

    shell_id: int

    def update_value_based_on_inputs(self, env: Environment):
        # first, check to see if there's a cache conflict
        for key in self.cached:
            # can't be a conflict if we're consistent wih this key
            if self.latest == self.cached[key]:
                continue
            # check to see if this cache key is a SUBSET of the input
            for file, version in key:
                if file not in self.inputs:
                    break
                if env.file_versions.get(file) != version:
                    break
            else:
                raise Exception(
                    "Cached key",
                    key,
                    "is an equal subset of latest input",
                    self.inputs,
                    "but the cached values are different",
                )
            # check to see if the cache key is a SUPERSET of the input
            for file in self.inputs:
                if (file, env.file_versions.get(file)) not in key:
                    break
            else:
                raise Exception(
                    "Cached key",
                    key,
                    "is an equal superset of latest input",
                    self.inputs,
                    "but the cached values are different",
                )

        self.cached[
            tuple((file, env.file_versions.get(file)) for file in self.inputs)
        ] = self.latest
        env.register_action(self)


@dataclass(eq=False)
class Sh(ActionWithInputs):
    inputs: List[File]
    latest: int = 0
    cached: Dict[Sequence[Tuple[File, int]], int] = field(
        init=False, default_factory=dict
    )

    def update_result(self, inputs: List[File]):
        self.inputs = inputs
        self.latest += 1

    def to_statements(self, env: Environment) -> List[str]:
        self.update_value_based_on_inputs(env)
        self.data = self.latest
        return [
            f"ctx.sh('python3 $RUN --mode=SH --id={self.shell_id}', env={env.get_env_vars()})"
        ]


@dataclass(eq=False)
class Input(ActionWithInputs):
    inputs: List[File]
    latest: List[Action]
    cached: Dict[Sequence[Tuple[File, int]], List[Action]] = field(
        init=False, default_factory=dict
    )

    def update_result(self, inputs: List[File], latest: List[Action]):
        self.inputs = inputs
        self.latest = latest

    @staticmethod
    def format_cache_key(file_versions: Sequence[Tuple[File, int]]):
        return set((file.path, version) for file, version in file_versions)

    def to_statements(self, env: Environment) -> List[str]:
        self.update_value_based_on_inputs(env)
        self.data = self.format_cache_key(
            [(file, env.file_versions[file]) for file in self.inputs]
        )
        out = [
            f"ret = eval(ctx.input(sh='python3 $RUN --mode=INPUT --id={self.shell_id}', env={env.get_env_vars()}).strip())"
        ]
        tester = "if"
        for (file_versions, actions) in self.cached.items():
            out.append(f"{tester} ret == {self.format_cache_key(file_versions)}:")
            out.extend(indent_action_list(actions, env))
            tester = "elif"

        out.append("else:")
        out.extend(indent_action_list([Failure()], env))

        return out


@dataclass
class Crash(Action):
    def to_statements(self, env: Environment) -> List[str]:
        return ["assert False"]


@dataclass
class Failure(Action):
    def to_statements(self, env: Environment) -> List[str]:
        return [f'print("{env.FAILURE}")', "assert False"]


class Environment:
    LOG_PATH = "log.txt"
    INPUT_PATH = "input.txt"
    BUILD_DIRECTORY = "build"
    FAILURE = "__FAILURE__"

    working_dir: str

    file_versions: Dict[File, int]
    file_cnt: int

    rule_cnt: int
    sh_cnt: int

    rules: List[Rule]
    actions: Dict[ActionWithInputs, ActionWithInputs]

    current_rule: Optional[Rule]

    def __init__(self, working_dir: str):
        self.working_dir = working_dir

        self.file_versions = {}
        self.file_cnt = 0

        self.rule_cnt = 0
        self.sh_cnt = 0

        self.rules = []
        self.actions = {}

        self.is_annotating = True

        mkdir(self.BUILD_DIRECTORY)
        sh("git", "init", cwd=self.BUILD_DIRECTORY)
        self._write_file("WORKSPACE")
        self.log(f"STARTING TEST")

    def _buildpath(self, path: str):
        return f"{self.BUILD_DIRECTORY}/{path}"

    def _write_file(self, path: str, contents: str = ""):
        with open(self._buildpath(path), "w") as f:
            f.write(contents)

    def _update_contents(self, file: File):
        self.file_versions[file] = self.file_versions.get(file, -1) + 1
        contents = f"V{self.file_versions[file]} ({file.path})"
        self._write_file(file.path, contents)
        return contents

    def register_action(self, action: ActionWithInputs):
        if action not in self.actions:
            self.actions[action] = action
            action.shell_id = self.sh_cnt
            self.sh_cnt += 1

    def get_env_vars(self):
        return {
            "RUN": os.path.join(os.path.dirname(os.path.abspath(__file__)), "run.py"),
            "LOG_PATH": os.path.abspath(self.LOG_PATH),
            "INPUT_PATH": os.path.abspath(self.INPUT_PATH),
            "OUTPUT_PATH": self.current_rule.output.path,
        }

    def log(self, msg: str):
        with open(self.LOG_PATH, "a") as f:
            print(msg, file=f)
        self.is_annotating = False

    def annotate(self, msg):
        if not self.is_annotating:
            self.log("")
        self.log("# " + msg)
        self.is_annotating = True

    def new_file(self):
        filename = f"f{self.file_cnt + 1}.txt"
        self.file_cnt += 1
        file = File(filename)
        contents = self._update_contents(file)
        self.log(f'CREATING FILE {filename} with contents: "{contents}"')
        return file

    def update_file(self, file: File):
        contents = self._update_contents(file)
        self.log(f'UPDATING FILE {file.path} with contents: "{contents}"')

    def delete_file(self, file: File):
        os.remove(self._buildpath(file.path))
        self.log(f"DELETING FILE {file.path}")

    def declare_rule(self, *actions) -> Rule:
        letter = chr(ord("A") + self.rule_cnt)
        self.rule_cnt += 1
        rule_name = f"Rule{letter}"
        out = File(f"{rule_name}.output")
        self.log(f"CREATING rule {rule_name}")
        rule = Rule(rule_name, list(actions), out)
        self.rules.append(rule)
        return rule

    def build(self, rule: Rule):
        if not self.is_annotating:
            self.log("")
        self.log(f"BUILDING rule {rule.name}")
        contents = "\n\n".join(rule.to_declaration(self) for rule in self.rules) + "\n"

        with open(self.INPUT_PATH, "w") as f:
            f.write(
                repr(
                    {
                        action.shell_id: dict(
                            inputs=[file.path for file in action.inputs],
                            data=action.data,
                        )
                        for action, _ in self.actions.items()
                    }
                )
            )

        self._write_file("BUILD", contents)
        try:
            output = sh(
                "bt",
                f":{rule.name}",
                "-q",
                quiet=True,
                cwd=self.BUILD_DIRECTORY,
                capture_output=True,
            ).decode("utf-8")
        except CalledProcessError as e:
            print(e.stdout.decode("utf-8"))
            raise

        if self.FAILURE in output:
            raise Exception("Unexpected scenario encountered")

        self.log(f"COMPLETED BUILDING rule {rule.name}\n")
        self.is_annotating = True

    def get_logs(self):
        with open(self.LOG_PATH) as f:
            return f.read()


@contextmanager
def create_test_env(snapshot):
    with tmp_directory(clean=True) as tmp:
        env = Environment(tmp)
        try:
            yield env
        finally:
            logs = env.get_logs()

    assert logs == snapshot

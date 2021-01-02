from threading import Lock
from typing import Dict

from execution import RuntimeRule
from fs_utils import get_repo_files
from loader import LoadedRule
from utils import BuildException


def generate_runtime_rules(
    target_rule_lookup: Dict[str, LoadedRule]
) -> Dict[str, RuntimeRule]:
    src_files = get_repo_files()
    preparing_to_runtime_rule_lookup = {}
    for rule in set(target_rule_lookup.values()):
        preparing_to_runtime_rule_lookup[rule] = RuntimeRule(
            name=str(rule),
            impl=rule.impl,
            outputs=rule.outputs,
            working_directory=rule.location,
            lock=Lock(),
            # to be filled in later
            remaining_rule_dependencies=[],
            dependents=[],
            inputs=[],
        )
    for loaded_rule, runtime_rule in preparing_to_runtime_rule_lookup.items():
        rule_dependencies = []
        inputs = []
        for dependency in loaded_rule.deps:
            inputs.append(dependency)
            if dependency in target_rule_lookup:
                # it is a generated file
                runtime_dependency = preparing_to_runtime_rule_lookup[
                    target_rule_lookup[dependency]
                ]
                runtime_dependency.dependents.append(runtime_rule)
                rule_dependencies.append(runtime_dependency)
            elif dependency in src_files:
                # it is a file within the repo and we already added it as an input, so do nothing
                pass
            else:
                raise BuildException(
                    f"Dependency `{dependency}` is not valid as it is neither a source file nor the output of another "
                    f"rule. "
                )
        runtime_rule.remaining_rule_dependencies = rule_dependencies
        runtime_rule.inputs = inputs

    return {
        target: preparing_to_runtime_rule_lookup[target_rule_lookup[target]]
        for target in target_rule_lookup
    }

from typing import List

from execution import RuntimeRule
from utils import BuildException


def find_needed_rules(target_rule: RuntimeRule):
    needed = set()
    start_actions = set()

    def find_dependencies(rule: RuntimeRule, dependents: List[RuntimeRule]):
        if rule in dependents:
            dependents.append(rule)
            raise BuildException(
                f"Circular dependency detected: Rule {rule} depends on itself "
                f"through the path: {' -> '.join(map(str, dependents))}"
            )
        dependents.append(rule)
        for dep in rule.remaining_rule_dependencies:
            find_dependencies(dep, dependents)
        dependents.pop()
        needed.add(rule)
        if not rule.remaining_rule_dependencies:
            start_actions.add(rule)

    find_dependencies(target_rule, [])
    return needed, start_actions

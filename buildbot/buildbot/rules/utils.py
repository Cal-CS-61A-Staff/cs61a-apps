from typing import List


class Action:
    """ "
    An expandable in the dependency graph
    """

    dependencies: List[Dependency]
    outputs: List[Output]

    def actions(self):
        ...

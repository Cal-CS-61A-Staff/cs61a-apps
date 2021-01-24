class BuildException(Exception):
    pass


# thrown internally by contexts to exit early, should always be caught
class CacheMiss(Exception):
    pass


class MissingDependency(Exception):
    def __init__(self, *paths: str):
        self.paths = paths

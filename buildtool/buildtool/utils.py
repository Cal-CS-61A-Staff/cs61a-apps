import hashlib


class BuildException(Exception):
    pass


# thrown internally by contexts to exit early, should always be caught
class CacheMiss(Exception):
    pass


class MissingDependency(Exception):
    def __init__(self, *paths: str):
        self.paths = paths


class HashState:
    def __init__(self):
        self._state = hashlib.md5()

    def update(self, data: bytes):
        self._state.update(str(len(data)).encode("utf-8") + b":")
        self._state.update(data + b":")
        return self

    def record(self, *args):
        self._state.update(str(args).encode("utf-8"))
        return self

    def state(self):
        return self._state.hexdigest()

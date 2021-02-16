import hashlib


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

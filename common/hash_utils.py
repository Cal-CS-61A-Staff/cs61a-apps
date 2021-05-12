import hashlib


class HashState:
    """Utility class for hashing data. Uses ``hashlib.md5``.

    :example usage:
    .. code-block:: python

        >>> state = HashState()
        >>> state.update(b"hello world")
        >>> state.state()
        'fe0cf2fe0d7cb366190a4a80af973909'
    """

    def __init__(self):
        self._state = hashlib.md5()

    def update(self, data: bytes):
        """Append some data to the current state.

        :param data: the data to append
        :type data: bytes

        :return: self
        """
        self._state.update(str(len(data)).encode("utf-8") + b":")
        self._state.update(data + b":")
        return self

    def record(self, *args):
        """Append multiple pieces of data to the current state.

        :param args: the data to append
        :type args: *str

        :return: self
        """
        self._state.update(str(args).encode("utf-8"))
        return self

    def state(self):
        """Get a hex digest of the current state.

        :return: the hex digest of the current state
        """
        return self._state.hexdigest()

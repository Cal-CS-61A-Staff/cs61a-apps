import os
import random
import string
from functools import wraps

from typing import Optional


def as_list(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        return list(func(*args, **kwargs))

    return wrapped


def sanitize_email(email):
    return email.replace("_", r"\_")


def dict_to_list(d):
    out = [None] * len(d)
    for k, v in d.items():
        out[int(k)] = v
    return out


def rand_id(length=32):
    return "".join(random.choices(string.ascii_uppercase, k=length))


def list_to_dict(l):
    return {i: x for i, x in enumerate(l)}


def rel_path(path):
    root = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(root, path)


def rel_open(path, *args, **kwargs):
    return open(rel_path(path), *args, **kwargs)


class IDFactory:
    def __init__(self, *, id_start="", id_end="", length=32, allow_random_ids=True):
        if length is None:
            length = 32
        self.length = length
        self.id_start = id_start
        self.id_end = id_end
        self.allow_random_ids = allow_random_ids
        self.current_ids = set()

    def id_from_str(self, string):
        return self.id_start + string + self.id_end

    def get_id(self, string: Optional[str] = None):
        if string is None:
            if not self.allow_random_ids:
                raise SyntaxError(
                    "A custom ID is required but was not set for this question!"
                )
            qid = rand_id(length=self.length)
            while qid in self.current_ids:
                qid = rand_id(length=self.length)
        else:
            qid = self.id_from_str(string)
            if qid in self.current_ids:
                raise SyntaxError(f"Received duplicate question IDs {qid}.")

        self.current_ids.add(qid)
        return qid

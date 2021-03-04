import random
import string
from functools import wraps


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

def list_to_dict(l):
    return {i: x for i, x in enumerate(l)}

class IDFactory:
    def __init__(self, id_start="", id_end="", length=32):
        self.length = length
        self.id_start = id_start
        self.id_end = id_end
        self.current_ids = set()

    def rand_id(self, length=None):
        return "".join(random.choices(string.ascii_uppercase, k=length))

    def id_from_str(self, string):
        return self.id_start + string + self.id_end

    def get_id(self, string=None):
        if string is None:
            qid = self.rand_id()
            while qid in self.current_ids:
                qid = self.rand_id()
        elif isinstance(string, str):
            qid = self.id_from_str(string)
            if qid in self.current_ids:
                raise SyntaxError(f"Received duplicate question ID's {qid}.")
        else:
            raise SyntaxError("ID must be a string or None!")

        self.current_ids.add(qid)
        return qid

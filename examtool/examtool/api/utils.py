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


def rand_id():
    return "".join(random.choices(string.ascii_uppercase, k=32))


def dict_to_list(d):
    out = [None] * len(d)
    for k, v in d.items():
        out[int(k)] = v
    return out


def list_to_dict(l):
    return {i: x for i, x in enumerate(l)}

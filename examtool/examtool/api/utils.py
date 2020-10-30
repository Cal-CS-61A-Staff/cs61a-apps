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

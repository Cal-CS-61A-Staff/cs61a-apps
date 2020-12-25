import queue
from functools import wraps
from threading import Thread


def only_once(f):
    q = queue.Queue()

    @wraps(f)
    def worker():
        while True:
            args, kwargs = q.get()
            f(*args, **kwargs)
            q.task_done()

    @wraps(f)
    def wrapped(*args, **kwargs):
        q.put([args, kwargs])

    Thread(target=worker, daemon=True).start()

    return wrapped

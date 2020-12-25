from collections import deque
from datetime import datetime

MAX_LOG_LEN = 100

logs = deque(maxlen=100)


def log(msg):
    print(msg)
    logs.append("{}: {}".format(datetime.now(), msg))


def get_log():
    return "\n".join(logs)

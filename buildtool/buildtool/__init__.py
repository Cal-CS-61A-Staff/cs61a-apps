import sys
import pathlib
from typing import Callable, Optional, Sequence, Union

sys.path.append(str(pathlib.Path(__file__).parent.absolute()))


"""
Below are some stubs to make imports in BUILD and rules.py files more pleasant
see loader.py for injected implementation
"""


def load(path: str):
    ...


def callback(
    *,
    name: Optional[str] = None,
    deps: Sequence[str] = (),
    impl: Callable,
    out: Union[str, Sequence[str]] = (),
):
    ...


def find(path: str, unsafe_ignore_extension=False):
    ...

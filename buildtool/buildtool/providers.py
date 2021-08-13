from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Callable, Iterable, List, Sequence, Union

from common.hash_utils import HashState
from fs_utils import hash_file
from utils import BuildException


class ProviderMetaclass(type):
    def __str__(self):
        return "<Provider>"


@dataclass
class AbstractProvider(metaclass=ProviderMetaclass):
    value: object


def provider(*args):
    if len(args) > 1:
        raise BuildException("provider() takes at most one argument")
    if args:

        class Provider(AbstractProvider):
            def __init__(self):
                super().__init__(args[0])

    else:

        class Provider(AbstractProvider):
            pass

    return Provider


@dataclass(frozen=True, eq=False, repr=False)
class DepSet:
    # children are either file paths, or depsets (NOT rules)
    children: Sequence[Union[DepSet, List[str]]]

    def __init__(self, *args: Union[DepSet, str]):
        object.__setattr__(self, "children", list(args))
        if any(
            ".cache" in arg or ".scratch" in arg for arg in args if isinstance(arg, str)
        ):
            raise BuildException("?", args)

    @lru_cache
    def _hash(self) -> str:
        print("[WARNING] DepSet hashing is experimental and may corrupt caches")
        hashstate = HashState()
        for child in self.children:
            if isinstance(child, DepSet):
                hashstate.record(child._hash())
            else:
                assert (
                    isinstance(child, str)
                    and not child.endswith("/")
                    and not child.endswith(":")
                ), "Depsets only hold files or other depsets"
                hashstate.record(child)
                hashstate.update(hash_file(child))
        return hashstate.state()

    def to_iter(self):
        explored = set()
        pending = [self]
        while pending:
            todo = pending.pop()
            if todo in explored:
                continue
            explored.add(todo)
            if isinstance(todo, DepSet):
                pending.extend(todo.children)
            else:
                yield f"//{todo}"


class LazyDepSet(DepSet):
    gen_children: Callable[[], Union[DepSet, List[str]]]

    def __init__(self, gen_children: Callable[[], Iterable[Union[DepSet, str]]]):
        assert callable(gen_children)
        object.__setattr__(self, "gen_children", gen_children)

    @property
    def children(self):
        if not hasattr(self, "_children"):
            forced = self.gen_children()
            object.__setattr__(
                self,
                "_children",
                forced if isinstance(forced, DepSet) else list(forced),
            )
        return self._children


class IterableDepSet(DepSet):
    def __iter__(self):
        return self.to_iter()

    def __add__(self, other: Union[DepSet, List[str]]):
        if isinstance(other, DepSet):
            return IterableDepSet(self, other)
        elif isinstance(other, list):
            return IterableDepSet(self, *other)
        return NotImplemented

    def __bool__(self):
        return any(True for _ in self)


class GlobDepSet(LazyDepSet, IterableDepSet):
    pass


TransitiveDepsProvider = provider()
TransitiveOutputProvider = provider()
DepsProvider = provider()
OutputProvider = provider()

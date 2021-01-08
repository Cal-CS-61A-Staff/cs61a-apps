import hashlib
import os
from pathlib import Path

from state import Rule
from utils import CacheMiss


def make_cache_fetcher(cache_directory: str):
    def cache_fetcher(state: str, target: str) -> str:
        dest = Path(cache_directory).joinpath(state).joinpath(target)
        try:
            with open(dest, "r") as f:
                return f.read()
        except FileNotFoundError:
            raise CacheMiss

    return cache_fetcher


def make_cache_memorize(cache_directory: str):
    def memorize(state: str, target: str, data: str):
        cache_target = Path(cache_directory).joinpath(state).joinpath(target)
        os.makedirs(os.path.dirname(cache_target), exist_ok=True)
        cache_target.write_text(data)

    return memorize


def get_cache_output_paths(cache_directory: str, rule: Rule, cache_key: str):
    cache_location = Path(cache_directory).joinpath(cache_key)
    keys = [
        hashlib.md5(output_path.encode("utf-8")).hexdigest()
        for output_path in rule.outputs
    ]
    for i, (output_path, key) in enumerate(zip(rule.outputs, keys)):
        if output_path.endswith("/"):
            keys[i] += "/"
    return cache_location, keys

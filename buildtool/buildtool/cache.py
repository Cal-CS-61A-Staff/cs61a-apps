import hashlib
import os
from os.path import dirname
from pathlib import Path
from typing import Iterator

from fs_utils import copy_helper
from google.cloud.exceptions import NotFound
from google.cloud.storage import Blob
from state import Rule
from utils import BuildException, CacheMiss

CLOUD_BUCKET_PREFIX = "gs://"


def get_bucket(cache_directory: str):
    if cache_directory.startswith(CLOUD_BUCKET_PREFIX):
        from google.cloud import storage

        client = storage.Client()
        return client.get_bucket(cache_directory[len(CLOUD_BUCKET_PREFIX) :])


def make_cache_fetcher(cache_directory: str):
    bucket = get_bucket(cache_directory)

    def cache_fetcher(state: str, target: str) -> str:
        if bucket:
            dest = str(Path(state).joinpath(target))
            try:
                return bucket.blob(dest).download_as_string().decode("utf-8")
            except NotFound:
                raise CacheMiss
        else:
            dest = Path(cache_directory).joinpath(state).joinpath(target)
            try:
                with open(dest, "r") as f:
                    return f.read()
            except FileNotFoundError:
                raise CacheMiss

    def cache_loader(cache_key: str, rule: Rule, dest_root: str) -> bool:
        cache_location, cache_paths = get_cache_output_paths(
            cache_directory, rule, cache_key
        )
        if bucket:
            del cache_location
            for src_name, cache_path in zip(rule.outputs, cache_paths):
                os.makedirs(dest_root, exist_ok=True)
                try:
                    if src_name.endswith("/"):
                        blobs: Iterator[Blob] = bucket.list_blobs(
                            prefix=cache_path, delimiter="/"
                        )
                        for blob in blobs:
                            target = str(
                                Path(dest_root)
                                .joinpath(src_name)
                                .joinpath(blob.path[len(cache_path) :])
                            )
                            os.makedirs(dirname(target), exist_ok=True)
                            blob.download_to_filename(target)
                    else:
                        target = str(Path(dest_root).joinpath(src_name))
                        os.makedirs(dirname(target), exist_ok=True)
                        bucket.blob(
                            str(Path(cache_key).joinpath(cache_path)),
                        ).download_to_filename(target)
                except NotFound:
                    return False
            return True
        else:
            if not os.path.exists(cache_location):
                return False
            try:
                copy_helper(
                    src_root=cache_location,
                    src_names=cache_paths,
                    dest_root=dest_root,
                    dest_names=rule.outputs,
                )
            except FileNotFoundError:
                raise BuildException(
                    "Cache corrupted. This should never happen unless you modified the cache "
                    "directory manually! If so, delete the cache directory and try again."
                )
            return True

    return cache_fetcher, cache_loader


def make_cache_memorize(cache_directory: str):
    bucket = get_bucket(cache_directory)

    def memorize(state: str, target: str, data: str):
        if bucket:
            bucket.blob(str(Path(state).joinpath(target))).upload_from_string(data)
        else:
            cache_target = Path(cache_directory).joinpath(state).joinpath(target)
            os.makedirs(os.path.dirname(cache_target), exist_ok=True)
            cache_target.write_text(data)

    def save(cache_key: str, rule: Rule, output_root: str):
        cache_location, cache_paths = get_cache_output_paths(
            cache_directory, rule, cache_key
        )

        memorize(cache_key, ".touch", "")

        if bucket:
            del cache_location  # just to be safe

            for src_name, cache_path in zip(rule.outputs, cache_paths):
                if src_name.endswith("/"):
                    for path, subdirs, files in os.walk(
                        Path(output_root).joinpath(src_name)
                    ):
                        for name in files:
                            bucket.blob(
                                str(
                                    Path(cache_key)
                                    .joinpath(cache_path)
                                    .joinpath(path)
                                    .joinpath(name)
                                )
                            ).upload_from_filename(
                                str(
                                    Path(output_root)
                                    .joinpath(src_name)
                                    .joinpath(path)
                                    .joinpath(name)
                                )
                            )
                else:
                    bucket.blob(
                        str(Path(cache_key).joinpath(cache_path)),
                    ).upload_from_filename(
                        str(Path(output_root).joinpath(src_name)),
                    )
        else:
            copy_helper(
                src_root=output_root,
                src_names=rule.outputs,
                dest_root=cache_location,
                dest_names=cache_paths,
            )

    return memorize, save


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

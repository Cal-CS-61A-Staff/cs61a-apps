import hashlib
import os
import traceback
from os.path import dirname
from pathlib import Path
from typing import Iterator

from fs_utils import copy_helper, hash_file
from google.cloud.exceptions import NotFound
from google.cloud.storage import Blob
from state import Rule
from utils import BuildException, CacheMiss

CLOUD_BUCKET_PREFIX = "gs://"
AUX_CACHE = ".aux_cache"

STATS = dict(hits=0, misses=0, inserts=0)


def get_bucket(cache_directory: str):
    if cache_directory.startswith(CLOUD_BUCKET_PREFIX):
        from google.cloud import storage

        client = storage.Client()
        return client.bucket(cache_directory[len(CLOUD_BUCKET_PREFIX) :])


def make_cache_fetcher(cache_directory: str, *, is_aux=False):
    bucket = get_bucket(cache_directory)
    delta = 1 if not is_aux else 0

    def cache_fetcher(state: str, target: str) -> str:
        if bucket:
            try:
                out = aux_fetcher(state, target)
                STATS["hits"] += delta
                return out
            except CacheMiss:
                dest = str(Path(state).joinpath(target))
                try:
                    out = bucket.blob(dest).download_as_string().decode("utf-8")
                    STATS["hits"] += delta
                except NotFound:
                    STATS["misses"] += delta
                    raise CacheMiss
                else:
                    # cache it on disk
                    aux_memorize(state, target, out)
                    return out
        else:
            dest = Path(cache_directory).joinpath(state).joinpath(target)
            try:
                with open(dest, "r") as f:
                    out = f.read()
                    STATS["hits"] += delta
                    return out
            except FileNotFoundError:
                STATS["misses"] += delta
                raise CacheMiss

    def cache_loader(cache_key: str, rule: Rule, dest_root: str) -> bool:
        cache_location, cache_paths = get_cache_output_paths(
            cache_directory, rule, cache_key
        )
        if bucket:
            del cache_location
            if not aux_loader(cache_key, rule, dest_root):
                try:
                    cache_fetcher(cache_key, ".touch")
                except CacheMiss:
                    STATS["misses"] += delta
                    return False
                for src_name, cache_path in zip(rule.outputs, cache_paths):
                    cache_path = str(Path(cache_key).joinpath(cache_path))
                    os.makedirs(dest_root, exist_ok=True)
                    try:
                        if src_name.endswith("/"):
                            os.makedirs(
                                Path(dest_root).joinpath(src_name), exist_ok=True
                            )
                            blobs: Iterator[Blob] = list(
                                bucket.list_blobs(prefix=cache_path)
                            )
                            for blob in blobs:
                                target = str(
                                    Path(dest_root)
                                    .joinpath(src_name)
                                    .joinpath(blob.name[len(cache_path) + 1 :])
                                )
                                os.makedirs(dirname(target), exist_ok=True)
                                blob.download_to_filename(target)
                                STATS["hits"] += delta
                        else:
                            target = str(Path(dest_root).joinpath(src_name))
                            os.makedirs(dirname(target), exist_ok=True)
                            bucket.blob(cache_path).download_to_filename(target)
                            STATS["hits"] += delta
                    except NotFound:
                        STATS["misses"] += delta
                        return False
                # now that we have fetched, let's cache it on disk
                aux_save(cache_key, rule, dest_root)
            return True
        else:
            if not os.path.exists(cache_location):
                STATS["misses"] += delta
                return False
            try:
                copy_helper(
                    src_root=cache_location,
                    src_names=cache_paths,
                    dest_root=dest_root,
                    dest_names=rule.outputs,
                )
                STATS["hits"] += delta
            except FileNotFoundError:
                raise BuildException(
                    "Cache corrupted. This should never happen unless you modified the cache "
                    "directory manually! If so, delete the cache directory and try again."
                )
            return True

    return cache_fetcher, cache_loader


def make_cache_memorize(cache_directory: str, *, is_aux=False):
    bucket = get_bucket(cache_directory)
    delta = 1 if not is_aux else 0

    def memorize(state: str, target: str, data: str):
        if bucket:
            try:
                prev_saved = aux_fetcher(state, target)
            except CacheMiss:
                prev_saved = None
            aux_memorize(state, target, data)
            if prev_saved != data:
                STATS["inserts"] += delta
                bucket.blob(str(Path(state).joinpath(target))).upload_from_string(data)
        else:
            cache_target = Path(cache_directory).joinpath(state).joinpath(target)
            os.makedirs(os.path.dirname(cache_target), exist_ok=True)
            STATS["inserts"] += delta
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
                    dir_root = Path(output_root).joinpath(src_name)
                    for path, subdirs, files in os.walk(dir_root):
                        path = os.path.relpath(path, dir_root)
                        for name in files:
                            #               output_root -> src_name/ -> [path -> name]
                            # <cache_base> -> cache_key -> cache_path -> [path -> name]
                            target = Path(path).joinpath(name)
                            src_loc = (
                                Path(output_root).joinpath(src_name).joinpath(target)
                            )
                            aux_cache_loc = (
                                Path(AUX_CACHE)
                                .joinpath(cache_key)
                                .joinpath(cache_path)
                                .joinpath(target)
                            )
                            if not os.path.exists(aux_cache_loc) or (
                                hash_file(src_loc) != hash_file(aux_cache_loc)
                            ):
                                STATS["inserts"] += delta
                                bucket.blob(
                                    str(
                                        Path(cache_key)
                                        .joinpath(cache_path)
                                        .joinpath(target)
                                    )
                                ).upload_from_filename(str(src_loc))
                else:
                    #                 output_root -> src_name
                    # <cache_base> -> cache_key -> cache_path

                    target = Path(output_root).joinpath(src_name)
                    aux_cache_loc = (
                        Path(AUX_CACHE).joinpath(cache_key).joinpath(cache_path)
                    )
                    if not os.path.exists(aux_cache_loc) or (
                        hash_file(target) != hash_file(aux_cache_loc)
                    ):
                        STATS["inserts"] += delta
                        bucket.blob(
                            str(Path(cache_key).joinpath(cache_path)),
                        ).upload_from_filename(
                            str(Path(output_root).joinpath(src_name)),
                        )

            aux_save(cache_key, rule, output_root)

        else:
            STATS["inserts"] += delta
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


aux_fetcher, aux_loader = make_cache_fetcher(AUX_CACHE, is_aux=True)
aux_memorize, aux_save = make_cache_memorize(AUX_CACHE, is_aux=True)

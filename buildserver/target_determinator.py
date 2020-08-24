import os
from typing import Iterable, Optional, Set, Union

from github.File import File


def get_app(path: Optional[str]):
    if path is None:
        return None
    path = os.path.normpath(path)
    folders = path.split(os.sep)
    if len(folders) <= 1:
        # not in any app folder
        return None

    return str(folders[0])


def determine_targets(files: Iterable[Union[File, str]]) -> Set[str]:
    modified_apps = []
    for file in files:
        if isinstance(file, str):
            modified_apps.append(get_app(file))
        else:
            modified_apps.append(get_app(file.filename))
            modified_apps.append(get_app(file.previous_filename))

    return set([app for app in modified_apps if app is not None])

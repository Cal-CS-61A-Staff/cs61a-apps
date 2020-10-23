import os
from collections import defaultdict

import click

from examtool.cli.utils import exam_name_option


@click.command()
@exam_name_option
def check_dupes(exam):
    """
    Search for PDFs submitted for multiple exams.
    If any are found, you must manually check that the correct one is uploaded to Gradescope.
    """
    files = defaultdict(list)
    for target in os.listdir("out/export"):
        if not target.startswith(exam):
            continue
        target = os.path.join("out/export", target)
        if not os.path.isdir(target):
            continue
        for file in os.listdir(target):
            if "@" not in file:
                continue
            files[file].append(target)
    for file, exams in files.items():
        if len(exams) > 1:
            print(file, exams)


if __name__ == "__main__":
    check_dupes()

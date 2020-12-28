import argparse

from formatter.formatter import prettify


def reformat_raw(src):
    return prettify([src])


def reformat_files(src, dest=None):
    with open(src) as src:
        formatted = prettify([src.read()])
    if dest:
        with open(dest, "w") as dest:
            dest.write(formatted + "\n")
    else:
        print(formatted)
    exit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CS61A Scheme Formatter - Summer 2019")

    parser.add_argument(
        "-r",
        "--reformat",
        type=str,
        nargs="*",
        help="Reformats file and writes to second argument, if exists, or to stdout, otherwise..",
        metavar="FILE",
    )

    args = parser.parse_args()

    reformat_files(*args.reformat)

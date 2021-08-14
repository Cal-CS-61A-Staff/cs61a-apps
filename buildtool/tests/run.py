#!env/bin/python3.8
import os
import sys

import click


@click.command()
@click.option("--mode", required=True)
@click.option("--id", "shell_id", type=int, required=True)
def main(mode: str, shell_id: int):
    log_path = os.getenv("LOG_PATH")
    in_scratch = ".scratch_" in os.path.abspath(os.curdir)
    with open(log_path, "a") as f:
        print(
            "RUNNING run.py",
            *sys.argv[1:],
            f"in scratch directory with files {sorted(os.listdir(os.curdir))}"
            if in_scratch
            else "in working directory",
            file=f,
        )

    input_path = os.getenv("INPUT_PATH")
    with open(input_path) as f:
        data = eval(f.read())[shell_id]

    # check we can see each of the specified inputs
    for inp in data["inputs"]:
        with open(inp):
            pass

    if mode == "INPUT":
        print(data["data"])
        return

    else:
        output = os.getenv("OUTPUT_PATH")
        if output:
            with open(output, "w") as f:
                f.write(f'V{data["data"]}')


if __name__ == "__main__":
    main()

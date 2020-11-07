import click


@click.group()
def cli():
    """
    This is an experimental general-purpose 61A task runner.
    """
    pass


if __name__ == "__main__":
    cli()

import click, sys, os

from common.rpc.auth_utils import get_token
from common.rpc.buildserver import trigger_build_sync

from github import Github
from github.GithubException import UnknownObjectException

APPS = "Cal-CS-61A-Staff/cs61a-apps"


@click.group("pr")
def pr():
    """
    Commands to interface with PRs.
    """
    pass


@pr.command()
@click.argument("num")
@click.argument("targets", nargs=-1)
def build(num, targets):
    """Build TARGETS for pull request NUM.

    NUM is the PR number you want to build targets
    for, and TARGETS is the list of apps you want
    to build within that PR. If no targets are passed
    in, then all apps modified in the PR are built.
    """
    repo = Github().get_repo(APPS)

    try:
        pull = repo.get_pull(int(num))
    except UnknownObjectException:
        raise Exception("Couldn't find that PR.")

    if pull.state == "closed":
        raise Exception("Cannot build targets for a closed PR!")

    print(f"PR {num}: {pull.title}")
    print(f"Building targets: {targets if targets else ['all']}")

    for target in targets:
        trigger_build_sync(
            pr_number=int(num),
            target_app=target,
            _impersonate="buildserver",
            noreply=True,
        )

    print("Build triggered!")

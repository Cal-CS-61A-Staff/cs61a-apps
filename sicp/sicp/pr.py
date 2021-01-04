import click, sys, os

from common.rpc.auth_utils import get_token, set_token_path
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
    set_token_path(f"{os.path.expanduser('~')}/.sicp_token")

    try:
        pull = repo.get_pull(int(num))
    except UnknownObjectException:
        print("Couldn't find that PR.", file=sys.stderr)
        exit(1)

    if pull.state == "closed":
        print("Cannot build targets for a closed PR!", file=sys.stderr)
        exit(1)

    print(f"PR {num}: {pull.title}")
    print(f"Building targets: {targets if targets else 'all'}")

    try:
        trigger_build_sync(
            pr_number=num,
            target_app=targets,
            _sudo_token=get_token(),
            _impersonate="buildserver",
        )
    except:
        print(f"You must be logged in as an admin to do that.", file=sys.stderr)
        exit(1)

from typing import Optional
from urllib.parse import urlparse

from github import Github
from github.PullRequest import PullRequest

from common.rpc.secrets import get_secret
from conf import GITHUB_BOT_USER


def get_github():
    return Github(get_secret(secret_name="GITHUB_ACCESS_TOKEN"))


def repo_name_from_packed_ref(packed_ref):
    repo_url, _ = unpack(packed_ref)
    return urlparse(repo_url).path.split(".")[0][1:]  # This is awful ... but it works


def set_pr_comment(text: str, pr: Optional[PullRequest]):
    if pr is None:
        return
    comments = pr.get_issue_comments()
    for comment in comments:
        if comment.user.login == GITHUB_BOT_USER:
            comment.edit(text)
            comment.update()
            break
    else:
        pr.create_issue_comment(text)


def pack(clone_url: str, sha: str) -> str:
    """
    Pack the source for a commit into a single str
    """
    return clone_url + "|" + sha


def unpack(packed_ref: str):
    return packed_ref.split("|")

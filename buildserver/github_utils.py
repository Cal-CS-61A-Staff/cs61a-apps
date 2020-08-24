from typing import Optional

from github.PullRequest import PullRequest

from env import GITHUB_BOT_USER


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

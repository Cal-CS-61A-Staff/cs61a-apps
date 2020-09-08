import re

import requests
from github import Github

from common.rpc.secrets import get_secret
from integration import Integration

VALID_PATH = r"[0-9A-Za-z\-]+"
REPO_REGEX = rf"(?P<repo>{VALID_PATH}/{VALID_PATH})"
PATH_REGEX = rf"(?P<path>{VALID_PATH})"

REGEX_TEMPLATE = (
    fr"(https?://)?github\.com/{REPO_REGEX}/pull/{PATH_REGEX}/?(\|[^\s|]+)?"
)

COURSE_ORGS = {"Cal-CS-61A-Staff": "cs61a"}

TRIGGER_WORDS = {
    "lgtm": "APPROVE",
    "sucks": "REQUEST_CHANGES",
    "needs changes": "REQUEST_CHANGES",
}


class LGTMIntegration(Integration):
    reply = None

    def _process(self):
        for trigger_word, event in TRIGGER_WORDS.items():
            if trigger_word in self._message.lower():
                break
        else:
            return

        match = re.search(REGEX_TEMPLATE, self._message)

        if not match:
            return

        try:
            repo = match.group("repo")
            pr = int(match.group("path"))
        except ValueError:
            return

        if COURSE_ORGS[repo.split("/")[0]] != self._course:
            return

        users = requests.get(
            "https://slack.com/api/users.list", params={"token": self._bot_token}
        ).json()

        g = Github(get_secret(secret_name="GITHUB_ACCESS_TOKEN"))
        repo = g.get_repo(repo)
        pr = repo.get_pull(pr)

        github_email = pr.user.list

        for member in users["members"]:
            if member["profile"].get("email") == github_email:
                break
        else:
            return

        for member in users["members"]:
            if member["id"] == self._event["user"]:
                sender_email = member["profile"].get("email")
                break
        else:
            return

        if sender_email == github_email:
            return

        action = "approved" if event == "APPROVE" else "requested changes on"

        pr.create_review(
            body="{} {} this PR via the Slackbot!".format(
                member["profile"].get("real_name_normalized"), action
            ),
            event=event,
        )

        if trigger_word == "lgtm":
            self.reply = ":white_check_mark: Automatically approved on GitHub!"
        elif trigger_word == "sucks":
            self.reply = ":poop: Wow, this really needs changes..."
        else:
            self.reply = ":x: Changes requested on GitHub!"

    @property
    def message(self):
        if self.reply:
            return self._message + "\n\n" + self.reply
        else:
            return self._message

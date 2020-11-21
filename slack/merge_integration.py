import re

import requests
from github import Github

from common.rpc.auth import read_spreadsheet
from common.rpc.secrets import get_secret
from integration import Integration

VALID_PATH = r"[0-9A-Za-z\-]+"
REPO_REGEX = rf"(?P<repo>{VALID_PATH}/{VALID_PATH})"
PATH_REGEX = rf"(?P<path>{VALID_PATH})"

REGEX_TEMPLATE = (
    fr"(https?://)?github\.com/{REPO_REGEX}/pull/{PATH_REGEX}/?(\|[^\s|]+)?"
)

COURSE_ORGS = {"Cal-CS-61A-Staff": "cs61a", "61c-teach": "cs61c"}

STAFF_GITHUB = {
    username: email
    for email, username in read_spreadsheet(
        course="cs61a",
        url="https://docs.google.com/spreadsheets/d/11f3e2Vszybnxcjipkx0WPYTgDvYadzIKEkz7Tb_48kg/",
        sheet_name="Sheet1",
    )[1:]
}


class MergeIntegration(Integration):
    reply = None

    def _process(self):
        if "merge" not in self._message.lower():
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

        if not pr.mergeable:
            self.reply = ":x: Cannot merge!"
            return

        if pr.user.login in STAFF_GITHUB:
            github_email = STAFF_GITHUB[pr.user.login]
        else:
            github_email = pr.user.email

        if not github_email:
            return

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

        if pr.merge():
            self.reply = ":heavy_check_mark: Merged into master!"
        else:
            self.reply = ":x: Failed to merge!"

    @property
    def message(self):
        if self.reply:
            return self._message + "\n\n" + self.reply
        else:
            return self._message

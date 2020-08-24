import re

import requests

from common.rpc.auth import list_admins
from integration import Integration

TAG_REGEX = r"@(?P<course>[a-zA-Z0-9]+)"


class GroupIntegration(Integration):
    @property
    def responses(self):
        users = None
        for match in re.finditer(TAG_REGEX, self._message):
            course = match.group("course")
            try:
                if course == "heads" or course == "admins":
                    course = self._course
                admins = list_admins(course=course)
            except:
                continue
            if not admins:
                continue
            users = (
                users
                or requests.get(
                    "https://slack.com/api/users.list",
                    params={"token": self._bot_token},
                ).json()
            )
            tags = []
            for member in users["members"]:
                for email, name in admins:
                    if (
                        member["profile"].get("email") == email
                        or member["profile"].get("real_name_normalized") == name
                    ):
                        tags.append("<@{}>".format(member["id"]))
            yield "Admins for {}: {}".format(course, ", ".join(tags))

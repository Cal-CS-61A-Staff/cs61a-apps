import re
from integration import Integration

VALID_PATH = r"[0-9A-Za-z\-]+"
PATH_REGEX = rf"(?P<path>{VALID_PATH})"

REGEX_TEMPLATE = (
    fr"(https?://)?github\.com/Cal-CS-61A-Staff/cs61a-apps/pull/{PATH_REGEX}/?(\|[^\s|]+)?"
)

class BuildIntegration(Integration):
    reply = None

    def _process(self):
        if "build" not in self._message.lower():
            return
            
        if "cs61a" != self._course:
            return

        match = re.search(REGEX_TEMPLATE, self._message)

        if not match:
            return

        try:
            pr = int(match.group("path"))
        except ValueError:
            return

        common.rpc.buildserver.trigger_build_sync(pr_number=pr, noreply=True)
        self.reply = ":white_check_mark: Build triggered!"

    @property
    def message(self):
        if self.reply:
            return self._message + "\n\n" + self.reply
        else:
            return self._message

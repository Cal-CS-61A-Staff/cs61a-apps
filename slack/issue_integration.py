import itertools
import re
from collections import namedtuple

from integration import Integration
from utils import OrderedSet

Issue = namedtuple("Issue", ["path"])

VALID_PATH = r"[0-9\-]"
PATH_REGEX = r"(?P<path>{}+)".format(VALID_PATH)

REGEX_TEMPLATE = (
    r"<(https?://)?github\.com/Cal-CS-61A-Staff/berkeley-cs61a/issues/{}/?(\|[^\s|]+)?>"
)
SHORT_REGEX_TEMPLATE = r"is/{}/?"


class IssueIntegration(Integration):
    def _process(self):
        self._issues = OrderedSet()
        for match in itertools.chain(
            re.finditer(REGEX_TEMPLATE.format(PATH_REGEX), self._message),
            re.finditer(SHORT_REGEX_TEMPLATE.format(PATH_REGEX), self._message),
        ):
            self._issues.add(Issue(match.group("path")))

    @property
    def message(self):
        out = self._message
        for issue in self._issues:
            out = re.sub(
                REGEX_TEMPLATE.format(issue.path), "is/{}".format(issue.path), out
            )
            out = re.sub(
                SHORT_REGEX_TEMPLATE.format(issue.path),
                r"<https://github.com/Cal-CS-61A-Staff/berkeley-cs61a/issues/{}|is/{}>".format(
                    issue.path, issue.path
                ),
                out,
            )
        return out

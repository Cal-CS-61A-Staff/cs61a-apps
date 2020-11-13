import itertools
import re
from collections import namedtuple

from integration import Integration
from utils import OrderedSet

AppsPrLink = namedtuple("AppsPrLink", ["path"])

VALID_PATH = r"[0-9A-Za-z\-]"
PATH_REGEX = r"(?P<path>{}+)".format(VALID_PATH)

REGEX_TEMPLATE = (
    r"<(https?://)?github\.com/Cal-CS-61A-Staff/cs61a-apps/pull/{}/?(\|[^\s|]+)?>"
)
SHORT_REGEX_TEMPLATE = r"apr/{}/?"


class AppsPRLinkIntegration(Integration):
    def _process(self):
        self._prlinks = OrderedSet()
        for match in itertools.chain(
            re.finditer(REGEX_TEMPLATE.format(PATH_REGEX), self._message),
            re.finditer(SHORT_REGEX_TEMPLATE.format(PATH_REGEX), self._message),
        ):
            self._prlinks.add(AppsPrLink(match.group("path")))

    @property
    def message(self):
        out = self._message
        for prlink in self._prlinks:
            out = re.sub(
                REGEX_TEMPLATE.format(prlink.path), "apr/{}".format(prlink.path), out
            )
            out = re.sub(
                SHORT_REGEX_TEMPLATE.format(prlink.path),
                r"<https://github.com/Cal-CS-61A-Staff/cs61a-apps/pull/{}|pr/{}>".format(
                    prlink.path, prlink.path
                ),
                out,
            )
        return out

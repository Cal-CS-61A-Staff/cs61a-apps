import itertools
import re
from collections import namedtuple

from integration import Integration
from utils import OrderedSet

GoLink = namedtuple("GoLink", ["path"])

VALID_PATH = r"[0-9A-Za-z\-]"
PATH_REGEX = r"(?P<path>{}+)".format(VALID_PATH)

REGEX_TEMPLATE = r"<(https?://)?go\.cs61a\.org/{}/?(\|[^\s|]+)?>"
SHORT_REGEX_TEMPLATE = r"go/{}/?"


class GoLinkIntegration(Integration):
    def _process(self):
        self._golinks = OrderedSet()
        for match in itertools.chain(
            re.finditer(REGEX_TEMPLATE.format(PATH_REGEX), self._message),
            re.finditer(SHORT_REGEX_TEMPLATE.format(PATH_REGEX), self._message),
        ):
            self._golinks.add(GoLink(match.group("path")))

    @property
    def message(self):
        out = self._message
        for golink in self._golinks:
            out = re.sub(
                REGEX_TEMPLATE.format(golink.path), "go/{}".format(golink.path), out
            )
            out = re.sub(
                SHORT_REGEX_TEMPLATE.format(golink.path),
                r"<https://go.cs61a.org/{}|go/{}>".format(golink.path, golink.path),
                out,
            )
        return out

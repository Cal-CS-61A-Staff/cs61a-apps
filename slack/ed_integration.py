import itertools
import re
from collections import namedtuple
from html import unescape

from common.rpc.auth import perform_ed_action, ed_course_id
from integration import Integration
from utils import OrderedSet

SHORT_REGEX = r"@(?P<num>[0-9]+)"
LONG_REGEX = (
    r"<(https?://)?edstem\.org/us/courses/{}\/discussion/(?P<pid>[0-9]+)(\|[^\s|]+)?>"
)

Post = namedtuple("Post", ["subject", "content", "url", "num", "pid"])


class EdIntegration(Integration):
    def _process(self):
        course_id = ed_course_id(course=self._course)
        ed_posts = perform_ed_action(
            action="get_feed",
            course=self._course,
            as_staff=True,
            kwargs=dict(limit=999999),
        )["threads"]

        self._posts = OrderedSet()
        for match in itertools.chain(
            re.finditer(SHORT_REGEX, self._message),
            re.finditer(LONG_REGEX.format(course_id), self._message),
        ):
            num = int(match.group("num"))
            pid = int(match.group("pid"))
            post = None
            if pid:
                for p in ed_posts:
                    if p.get("id", 0) == pid:
                        post = p
                        break
            elif num:
                for p in ed_posts:
                    if p.get("number", 0) == num:
                        post = p
                        break
            if not post:
                continue
            subject = post["title"]
            content = post["document"]

            subject = unescape(subject)
            content = unescape(re.sub("<[^<]+?>", "", content))
            url = "https://edstem.org/us/courses/{}/discussion/{}".format(
                course_id, post["id"]
            )

            self._posts.add(Post(subject, content, url, post["number"], post["id"]))

    @property
    def message(self):
        out = self._message
        for post in self._posts:
            shortform = "@{}".format(post.num)
            link = "<{}|@{}>".format(post.url, post.num)
            out = out.replace("<{}>".format(post.url), shortform)
            out = out.replace("<{}|{}>".format(post.url, post.url), shortform)
            out = out.replace(shortform, link)
        return out

    @property
    def attachments(self):
        return [
            {
                "color": "#3575a8",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": ":piazza: *<{}|{}>* \n {}".format(
                                post.url, post.subject, post.content[:2500]
                            ),
                        },
                        "accessory": {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Open"},
                            "value": "piazza_open_click",
                            "url": post.url,
                        },
                    }
                ],
            }
            for post in self._posts
        ]

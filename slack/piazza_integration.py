import itertools
import re
from collections import namedtuple
from html import unescape

from common.rpc.auth import perform_piazza_action, piazza_course_id
from integration import Integration
from utils import OrderedSet

SHORT_REGEX = r"@(?P<cid>[0-9]+)(_f(?P<fid>[0-9]+))?"
LONG_REGEX = r"<(https?://)?piazza\.com/class/{}\?cid=(?P<cid>[0-9]+)(_f(?P<fid>[0-9]+))?(\|[^\s|]+)?>"

Post = namedtuple("Post", ["subject", "content", "url", "full_cid"])


class PiazzaIntegration(Integration):
    def _process(self):
        course_id = piazza_course_id(course=self._course)

        self._posts = OrderedSet()
        for match in itertools.chain(
            re.finditer(SHORT_REGEX, self._message),
            re.finditer(LONG_REGEX.format(course_id), self._message),
        ):
            cid = int(match.group("cid"))
            fid_str = match.group("fid")
            full_cid = match.group("cid") + ("_f{}".format(fid_str) if fid_str else "")
            post = perform_piazza_action(
                action="get_post",
                course=self._course,
                as_staff=True,
                kwargs=dict(cid=cid),
            )
            subject = post["history"][0]["subject"]
            content = post["history"][0]["content"]

            if fid_str:
                fid = int(fid_str)  # 1 indexed
                curr_id = 0
                for child in post["children"]:
                    if child["type"] != "followup":
                        continue
                    curr_id += 1
                    if fid == curr_id:
                        break
                else:
                    return
                content = child["subject"]

            subject = unescape(subject)
            content = unescape(re.sub("<[^<]+?>", "", content))
            url = "https://piazza.com/class/{}?cid={}".format(course_id, full_cid)

            self._posts.add(Post(subject, content, url, full_cid))

    @property
    def message(self):
        out = self._message
        for post in self._posts:
            shortform = "@{}".format(post.full_cid)
            link = "<{}|@{}>".format(post.url, post.full_cid)
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

from common.rpc.auth import Network, perform_ed_action


class EdNetwork(Network):
    def __init__(self, course, is_staff, is_test):
        super().__init__(course, is_staff, is_test, perform_ed_action)

    def get_unresolved(self):
        feed = self.get_feed(limit=999999)["threads"]
        unresolved = unresolved_followups = 0
        for post in feed:
            u = post.get("is_answered", False)
            uf = post.get("unresolved_count", 0)
            if u and not uf:
                continue

            title = post["title"]
            if "EC" in title or "extra credit" in title.lower():
                continue
            unresolved += u
            unresolved_followups += uf
        return unresolved, unresolved_followups

    def iter_all_posts(self, limit=None):  # new
        """Get all posts visible to the current user
        This grabs you current feed and ids of all posts from it; each post
        is then individually fetched. This method does not go against
        a bulk endpoint; it retrieves each post individually, so a
        caution to the user when using this.
        :type limit: int|None
        :param limit: If given, will limit the number of posts to fetch
            before the generator is exhausted and raises StopIteration.
        :returns: An iterator which yields all posts which the current user
            can view
        :rtype: generator
        """
        feed = self.get_feed(limit=999999)
        cids = [post["id"] for post in feed["threads"]]
        if limit:
            cids = cids[:limit]
        for cid in cids:
            yield self.get_post(cid=cid)

    def list_unresolved(self):  # new
        """Returns a generator of all unresolved posts"""
        feed = self.get_feed(limit=999999)
        post_snippets = feed.get("threads")

        for s in post_snippets:
            if not s.get("is_answered", False) or s.get("unresolved_count", 0):
                cid = s["id"]
                yield self.get_post(cid=cid)


network = EdNetwork("cs61a", True, False)

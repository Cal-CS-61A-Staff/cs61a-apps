from common.rpc.auth import PiazzaNetwork


class Network(PiazzaNetwork):
    def get_unresolved(self):
        feed = self.get_feed(limit=999999, offset=0)["feed"]
        unresolved = unresolved_followups = 0
        for post in feed:
            u = post.get("no_answer", 0)
            uf = post.get("no_answer_followup", 0)
            if not u and not uf:
                continue

            subject = post["subject"]
            if "EC" in subject or "extra credit" in subject.lower():
                continue
            unresolved += u
            unresolved_followups += uf
        return unresolved, unresolved_followups

    def iter_all_posts1(self, limit=None):  # new
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
        feed = self.get_feed(limit=999999, offset=0)
        cids = [post["id"] for post in feed["feed"]]
        if limit:
            cids = cids[:limit]
        for cid in cids:
            yield self.get_post(cid=cid)

    def list_unresolved(self): # new
        """Returns a generator of all unresolved posts"""
        feed = self.get_feed(limit=999999, offset=0)
        post_snippets = feed.get('feed')

        for s in post_snippets:
            if s.get('no_answer', False) or s.get('no_answer_followup', False):
                cid = s['id']
                yield self.get_post(cid=cid)


network = Network("cs61a", True, False)

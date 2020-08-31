
import requests, os
client_name, secret = os.environ['CLIENT_NAME'], os.environ['SECRET']



class Network:
    def __init__(self, client_name, secret, is_test):
        self.client_name = client_name
        self.secret = secret
        self.is_test = is_test

    def __getattr__(self, method):
        def bound_method(**kwargs):
            resp = requests.post("https://auth.apps.cs61a.org/piazza/{}".format(method), json={
                **kwargs,
                "client_name": self.client_name,
                "secret": self.secret,
                "staff": True,
                "test": self.is_test,
            })
            if resp.status_code != 200 and resp.text:
                raise Exception(resp.text)
            resp.raise_for_status()
            return resp.json()
        return bound_method

    def get_unresolved(self):
        feed = self.get_feed(limit=999999, offset=0)['feed']
        unresolved = unresolved_followups = 0
        for post in feed:
            u = post.get('no_answer', 0)
            uf = post.get('no_answer_followup', 0)
            if not u and not uf:
                continue

            subject = post["subject"]
            if "EC" in subject or "extra credit" in subject.lower():
                continue
            unresolved += u
            unresolved_followups += uf
        return unresolved, unresolved_followups

    def iter_all_posts1(self, limit=None): # new
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
        cids = [post['id'] for post in feed["feed"]]
        if limit:
            cids = cids[:limit]
        for cid in cids:
            yield self.get_post(cid=cid)

    def list_unresolved(self): # new
        """Returns a generator of all unresolved posts"""
        for post in self.iter_all_posts1():
            if post.get('no_answer', 0) or post.get('no_answer_followup', 0):
                yield post


network = Network(client_name, secret, False)

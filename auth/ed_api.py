import requests


class Ed:
    BASE = "https://us.edstem.org/api"
    FEED = "/threads?limit={limit}&sort=date&order=desc"
    THREAD = BASE + "/threads/{cid}?view=1"

    def user_login(self, username, password):
        resp = requests.post(
            Ed.BASE + "/token", json=dict(login=username, password=password)
        )
        self.token = resp.json()["token"]

    def network(self, id):
        self.course_endpoint = Ed.BASE + f"/courses/{id}"
        return self

    def get_feed(self, limit):
        resp = requests.get(
            self.course_endpoint + Ed.FEED.format(limit=limit),
            headers={"x-token": self.token},
        )
        return resp.json()

    def get_post(self, cid):
        resp = requests.get(Ed.THREAD.format(cid=cid), headers={"x-token": self.token})
        return resp.json()["thread"]

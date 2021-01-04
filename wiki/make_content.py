import os, yaml, requests
from shutil import copyfile

with open("metadata.yaml") as md:
    metadata = yaml.load(md)

metadata = metadata if metadata else {}
users = {}


def get_name(user):
    if user not in users:
        users[user] = (
            requests.get(f"https://api.github.com/users/{user}").json().get("name", "")
        )
    return users[user]


def get_user(user):
    name = get_name(user)
    if name:
        return f"{name} (@{user})"
    return f"@{user}"


class WikiApp:
    def __init__(self, path, name=None, dest=None):
        self.path = path
        with open(f"../{self.path}/README.md") as r:
            self.lines = [l for l in r.readlines()]

        self.name = name if name else self.lines[0][2:-1]
        self.dest = dest if dest else f"{self.path}/_index.md"
        self.contrib = metadata.get(path, [])

        self.contrib = [
            f"<a href='https://github.com/{contrib}'>{get_user(contrib)}</a>"
            for contrib in self.contrib
        ]


EXCLUDE = set(["node_modules", ".pytest_cache", "env"])

PATHS = {
    "examtool": WikiApp("examtool", "Examtool"),
    "exam-write": WikiApp("exam-write", "Writing Exams", dest="examtool/writing.md"),
    "oh": WikiApp("oh", "Office Hours Queue"),
    "oh/migrations": WikiApp(
        "oh/migrations", "Generating Migrations", dest="oh/migrations.md"
    ),
    "sicp": WikiApp("sicp", "SICP"),
    "piazzaoncall": WikiApp("piazzaoncall", "Piazza Oncall"),
}

if not os.path.exists("content"):
    os.makedirs("content")

with open("content/_index.md", "w") as index:
    index.write("\n# CS 61A Infra Wiki\n")
    index.write("Welcome to the CS 61A Infrastructure Wiki!\n")

apps = []
for root, dirs, files in os.walk("../"):
    dirs[:] = [d for d in dirs if d not in EXCLUDE]
    if root == "../wiki":
        dirs[:] = []
    for file in files:
        if file == "README.md":
            apps.append(root[3:])

for app_raw in apps:
    app = PATHS.get(app_raw, WikiApp(app_raw))
    print(app_raw)

    if not os.path.exists(f"content/{app.dest.split('/')[0]}"):
        os.makedirs(f"content/{app.dest.split('/')[0]}")

    with open(f"content/{app.dest}", "w") as c:
        c.write("---\n")
        c.write(f"title: {app.name}\n")
        c.write(f"contrib: {app.contrib}\n")
        c.write("---\n\n")
        for l in app.lines[1:]:
            c.write(f"{l}")

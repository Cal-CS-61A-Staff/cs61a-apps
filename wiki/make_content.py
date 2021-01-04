import os, yaml, requests
from shutil import copyfile

with open("metadata.yaml") as md:
    metadata = yaml.load(md)

metadata = metadata if metadata else {}
users = {
    "rahularya50": "Rahul Arya",
    "itsvs": "Vanshaj Singhania",
    "AnimeshAgrawal": "Animesh Agrawal",
}


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
            f"<a href='https://github.com/{contrib}' target='_blank'>{get_user(contrib)}</a>"
            for contrib in self.contrib
        ]


class StubApp:
    def __init__(self, path, name=None, description=None):
        self.path = path
        self.lines = (
            description.split("\n")
            if description
            else ["", "This app has not yet been documented."]
        )
        self.name = name if name else self.path.replace("-", " ").title()
        self.name += " (Stub)"
        self.dest = f"{self.path}/_index.md"
        self.contrib = metadata.get(path, [])

        self.contrib = [
            f"<a href='https://github.com/{contrib}' target='_blank'>{get_user(contrib)}</a>"
            for contrib in self.contrib
        ]


EXCLUDE = set(["node_modules", ".pytest_cache", "env"])

PATHS = {
    "auth": WikiApp("auth", "Auth"),
    "code": WikiApp("code", "Code"),
    "examtool": WikiApp("examtool", "Examtool"),
    "exam-write": WikiApp("exam-write", "Writing Exams", dest="examtool/writing.md"),
    "grade-display": WikiApp("grade-display", "Grade Display"),
    "howamidoing": WikiApp("howamidoing", "Howamidoing"),
    "oh": WikiApp("oh", "Office Hours Queue"),
    "oh/migrations": WikiApp(
        "oh/migrations", "Generating Migrations", dest="oh/migrations.md"
    ),
    "sicp": WikiApp("sicp", "SICP"),
    "piazzaoncall": WikiApp("piazzaoncall", "Piazza Oncall"),
}

if not os.path.exists("content"):
    os.makedirs("content")

INDEX = """# CS 61A Infra Wiki

Welcome to the CS 61A Infrastructure Wiki! This
wiki contains information about how various CS 61A
software works and how you can contribute to it.
We also plan on including installation guides so
that you can use these tools in your own courses.

This is a work in progress, so please *bear* with
us while we put it together! Apps marked `(Stub)`
are currently missing documentation but are
included to credit the code writers.
"""

with open("content/_index.md", "w") as index:
    index.write(INDEX)

apps = []
for root, dirs, files in os.walk("../"):
    dirs[:] = [d for d in dirs if d not in EXCLUDE]
    if root == "../wiki":
        dirs[:] = []
    for file in files:
        if file == "README.md":
            apps.append(root[3:])


def write_app(app):
    if not os.path.exists(f"content/{app.dest.split('/')[0]}"):
        os.makedirs(f"content/{app.dest.split('/')[0]}")

    with open(f"content/{app.dest}", "w") as c:
        c.write("---\n")
        c.write(f"title: {app.name}\n")
        c.write(f"contrib: {app.contrib}\n")
        c.write("---\n\n")
        for l in app.lines[1:]:
            c.write(f"{l}")


for app_raw in apps:
    app = PATHS.get(app_raw, WikiApp(app_raw))
    print(app_raw)
    write_app(app)

STUBS = [
    StubApp("buildserver"),
    StubApp("common"),
    StubApp("domains"),
    StubApp("hog-contest"),
    StubApp("indexer"),
    StubApp("logs"),
    StubApp("partnermatcher", name="Partner Matcher"),
    StubApp("paste"),
    StubApp("search"),
    StubApp("secrets"),
    StubApp("sections"),
    StubApp("shortlinks"),
    StubApp("slack", name="Slackbot"),
    StubApp("static-server"),
    StubApp("wiki"),
]

for app in STUBS:
    print(app.path)
    write_app(app)

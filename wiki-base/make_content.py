import os
from shutil import copyfile


class WikiApp:
    def __init__(self, path, name=None, dest=None):
        self.path = path
        with open(f"../{self.path}/README.md") as r:
            self.lines = [l for l in r.readlines()]

        self.name = name if name else self.lines[0][2:-1]
        self.dest = dest if dest else f"{self.path}/_index.md"


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
    "pr_proxy": WikiApp("pr_proxy", "PR Proxy"),
}

if not os.path.exists("content"):
    os.makedirs("content")

apps = []
for root, dirs, files in os.walk("../"):
    dirs[:] = [d for d in dirs if d not in EXCLUDE]
    if root == "../wiki-base":
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
        c.write("---\n\n")
        for l in app.lines[1:]:
            c.write(f"{l}")

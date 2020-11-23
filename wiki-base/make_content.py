import os
from shutil import copyfile

EXCLUDE = set(["node_modules", ".pytest_cache", "env"])

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

for app in apps:
    print(app)
    with open(f"../{app}/README.md") as r:
        lines = [l for l in r.readlines()]
        name, brief = lines[0][2:-1], lines[1][:-1]

    if not os.path.exists(f"content/{app}"):
        os.makedirs(f"content/{app}")

    with open(f"content/{app}/_index.md", "w") as i:
        i.write("---\n")
        i.write(f"title: {name}\n")
        i.write("---\n\n")
        i.write(f"{brief}\n")

    with open(f"content/{app}/readme.md", "w") as c:
        c.write("---\n")
        c.write(f"title: README\n")
        c.write("---\n\n")
        for l in lines[2:]:
            c.write(f"{l}")

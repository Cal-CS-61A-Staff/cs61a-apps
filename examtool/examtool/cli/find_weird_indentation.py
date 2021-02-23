from json import load

with open("cs61a-mt1-regular_submissions.json") as f:
    submissions = load(f)

weirded = []

try:
    for email in submissions:
        for question in submissions[email]:
            if (
                "\t" in submissions[email][question]
                and "  " in submissions[email][question]
            ):
                print(email)
                value = submissions[email][question]
                print()
                print(value.replace("\t", " "))
                value = value.replace("\t", "TAB>")
                print()
                print(value)
                d = input("?")
                if d:
                    weirded.append(email)
                    break
except KeyboardInterrupt:
    print(weirded)
    exit(0)

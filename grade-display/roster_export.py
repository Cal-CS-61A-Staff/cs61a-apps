import requests, auth, sys

COURSE_CODE = "cs61a"
SEMESTER = "fa20"

def export(app):
    OK_SERVER = "https://okpy.org"
    ENDPOINT = "/api/v3/course/cal/{cc}/{sem}/roster".format(cc=COURSE_CODE, sem=SEMESTER)
    FILE_PATH = "data/roster.csv"

    access_token = auth.get_token(app)

    print("Getting roster...")
    roster = requests.get(OK_SERVER + ENDPOINT, params={"access_token": access_token}).json()
    
    if "roster" in roster["data"]:
        roster = roster["data"]["roster"]
    else:
        print(roster["message"])
        sys.exit(1)

    print("Saving roster...")
    with open(FILE_PATH, 'w') as f:
        f.write(roster)
    print("Done.")

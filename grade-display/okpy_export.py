import requests, auth, sys
from common.rpc.auth import get_endpoint


def export():
    OK_SERVER = "https://okpy.org"
    ENDPOINT = f"/api/v3/course/{get_endpoint(course='cs61a')}/grades"
    FILE_PATH = "data/okpy_grades.csv"

    access_token = auth.get_token()

    print("Getting grades...")
    grades = requests.get(
        OK_SERVER + ENDPOINT, params={"access_token": access_token}
    ).json()

    if "grades" in grades["data"]:
        grades = grades["data"]["grades"]
    else:
        print(grades["message"])
        sys.exit(1)

    print("Saving grades...")
    with open(FILE_PATH, "w") as f:
        f.write(grades)
    print("Done.")

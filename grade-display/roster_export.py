import requests, auth, sys
from common.rpc.auth import get_endpoint


def export():
    OK_SERVER = "https://okpy.org"
    ENDPOINT = f"/api/v3/course/{get_endpoint(course='cs61a')}/roster"
    FILE_PATH = "data/roster.csv"

    access_token = auth.get_token()

    print("Getting roster...")
    roster = requests.get(
        OK_SERVER + ENDPOINT, params={"access_token": access_token}
    ).json()

    if "roster" in roster["data"]:
        roster = roster["data"]["roster"]
    else:
        print(roster["message"])
        sys.exit(1)

    print("Saving roster...")
    with open(FILE_PATH, "w") as f:
        f.write(roster)
    print("Done.")

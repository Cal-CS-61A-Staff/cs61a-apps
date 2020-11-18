from subprocess import Popen, PIPE
import requests, auth, argparse, sys

COURSE_CODE = "cs61a"
SEMESTER = "fa20"

def export(token=None, no_browser=False, debug=False):
    OK_SERVER = "https://okpy.org"
    ENDPOINT = "/api/v3/course/cal/{cc}/{sem}/roster"
    FILE_PATH = "data/roster{test}.csv"

    if debug:
        OK_SERVER = "http://localhost:5000"
        ENDPOINT = ENDPOINT.format(cc=COURSE_CODE, sem="sp16")
        FILE_PATH = FILE_PATH.format(test="_test")
    else:
        ENDPOINT = ENDPOINT.format(cc=COURSE_CODE, sem=SEMESTER)
        FILE_PATH = FILE_PATH.format(test="")

    access_token = token if token else auth.authenticate(debug, no_browser)

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

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--token', type=str, help='a pre-fetched token to use for okpy access')
    parser.add_argument('--no-browser', help='whether to use a browser for token fetch or not', action="store_true")
    parser.add_argument('--debug', help='whether to use a local ok server', action="store_true")

    args = parser.parse_args()
    export(args.token, args.no_browser, args.debug)

from subprocess import Popen, PIPE
import requests, auth, argparse, sys

COURSE_CODE = "cs61a"
SEMESTER = "fa20"

def export(token=None, no_browser=False, debug=False):
    OK_SERVER = "https://okpy.org"
    ENDPOINT = "/api/v3/course/cal/{cc}/{sem}/grades"
    FILE_PATH = "data/okpy_{fp}.csv"

    if debug:
        OK_SERVER = "http://localhost:5000"
        ENDPOINT = ENDPOINT.format(cc=COURSE_CODE, sem="sp16")
        FILE_PATH = FILE_PATH.format(fp="test")
    else:
        ENDPOINT = ENDPOINT.format(cc=COURSE_CODE, sem=SEMESTER)
        FILE_PATH = FILE_PATH.format(fp="grades")

    access_token = token if token else auth.authenticate(debug, no_browser)

    print("Getting grades...")
    grades = requests.get(OK_SERVER + ENDPOINT, params={"access_token": access_token}).json()
    
    if "grades" in grades["data"]:
        grades = grades["data"]["grades"]
    else:
        print(grades["message"])
        sys.exit(1)

    print("Saving grades...")
    with open(FILE_PATH, 'w') as f:
        f.write(grades)
    print("Done.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--token', type=str, help='a pre-fetched token to use for okpy access')
    parser.add_argument('--no-browser', help='whether to use a browser for token fetch or not', action="store_true")
    parser.add_argument('--debug', help='whether to use a local ok server', action="store_true")

    args = parser.parse_args()
    export(args.token, args.no_browser, args.debug)

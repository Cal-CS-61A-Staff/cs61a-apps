import pandas as pd, sys

from getpass import getpass
from pathlib import Path

from fullGSapi.api.gs_api_client import GradescopeAPIClient
from fullGSapi.api.client import GradescopeClient

from common.rpc.secrets import get_secret

pd.options.mode.chained_assignment = None

# Gradescope login credentials, if saved
CREDENTIALS = Path('credentials.txt')

# Change these every semester
COURSE_CODE = "185229"
ASSIGNMENTS = {'mt1': '673189', 'mt2': '800596'}

def export(assignment = None):
    if CREDENTIALS.exists():
        print("Using credentials file.")
        with open(CREDENTIALS) as f:
            email, password = f.readlines()
    else:
        email = "cs61a@berkeley.edu"
        password = get_secret(secret_name="GRADESCOPE_PW")
    email, password = email.strip(), password.strip()

    print("Logging in...")

    gsapi = GradescopeAPIClient()
    if gsapi.log_in(email, password):
        gs = GradescopeClient()
        if gs.log_in(email, password):
            print("Logged in.\n")
        else:
            print("Frontend login failed :(")
            sys.exit(1)
    else:
        print("Backend login failed :(")
        sys.exit(1)

    if not assignment:
        assignment = input(f'Assignment ({", ".join(list(ASSIGNMENTS.keys()))}): ')
    assign_num = ASSIGNMENTS[assignment]

    print(f"Looking up {assignment}...")
    name = gs.get_assignment_name(COURSE_CODE, assign_num)

    if not name:
        print("Assignment not found :(")
        sys.exit(1)

    print("Assignment found. Downloading scores...")
    res = gs.download_scores(COURSE_CODE, assign_num)

    if res:
        p = Path('.').expanduser().absolute()
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
        if not p.is_file():
            p = p.joinpath(f"data/{assignment}.csv")
        
        with open(p, 'wb+') as f:
            f.write(res)
        print("Done.\n")
    else:
        print("Download failed :(")
        sys.exit(1)

    print("Converting to Okpy upload file...")
    gs_csv = pd.read_csv(f"data/{assignment}.csv")
    ok_csv = gs_csv[['SID', 'Email','Total Score']]
    ok_csv['SID'] = ok_csv['SID'].fillna(0).astype(int).astype(str)

    ok_csv.to_csv(f"data/{assignment}.csv", index=False)
    print("Done.")

if __name__ == "__main__":
    if len(sys.argv) == 2:
        export(sys.argv[1])
    else:
        export()

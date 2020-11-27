import pandas as pd, sys

from getpass import getpass
from pathlib import Path

from fullGSapi.api.gs_api_client import GradescopeAPIClient
from fullGSapi.api.client import GradescopeClient

from common.rpc.secrets import get_secret

pd.options.mode.chained_assignment = None

# Change this every semester
COURSE_CODE = "185229"


def export(name, gs_code):
    email = "cs61a@berkeley.edu".strip()
    password = get_secret(secret_name="GRADESCOPE_PW").strip()

    print("Logging in...")

    gsapi = GradescopeAPIClient()
    if gsapi.log_in(email, password):
        gs = GradescopeClient()
        if gs.log_in(email, password):
            print("Logged in.\n")
        else:
            print("Frontend login failed :(", file=sys.stderr)
            sys.exit(1)
    else:
        print("Backend login failed :(", file=sys.stderr)
        sys.exit(1)

    print(f"Looking up {name}...")
    full_name = gs.get_assignment_name(COURSE_CODE, gs_code)

    if not full_name:
        print(f"Assignment for '{name}' not found :(", file=sys.stderr)
        sys.exit(1)

    print(f"Assignment '{full_name}' found. Downloading scores...")
    res = gs.download_scores(COURSE_CODE, gs_code)

    if res:
        p = Path(".").expanduser().absolute()
        if not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
        if not p.is_file():
            p = p.joinpath(f"data/{name}.csv")

        with open(p, "wb+") as f:
            f.write(res)
        print("Done.\n")
    else:
        print(f"Download for '{full_name}' failed :(", file=sys.stderr)
        sys.exit(1)

    print("Converting to Okpy upload file...")
    gs_csv = pd.read_csv(f"data/{name}.csv")
    ok_csv = gs_csv[["SID", "Email", "Total Score"]]
    ok_csv["SID"] = ok_csv["SID"].fillna(0).astype(int).astype(str)

    ok_csv.to_csv(f"data/{name}.csv", index=False)
    print("Done.")

    return full_name

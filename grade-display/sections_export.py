import requests, csv
#from common.rpc.secrets import get_secret
from common.rpc.sections import rpc_export_attendance

#CLIENT_SECRET = get_secret(secret_name="AUTH_SECRET")
URL = "https://tutorials.cs61a.org/api/export_attendance_secret"


def export():
    print("Getting tutorial attendance...")
#    raw = requests.post(URL, json={"full": False, "secret": CLIENT_SECRET}).json()[
#        "data"
#    ]["custom"]["attendances"]

    raw = rpc_export_attendance(full=True)["custom"]["attendances"]
    c = csv.reader(raw)

    print("Saving tutorial attendance...")
    with open("data/tutorials.csv", "w") as f:
        f.write("Email,Tutorial Attendance (Total)\n")
        f.write(raw)
    print("Done.")


if __name__ == "__main__":
    export()

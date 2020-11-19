import requests, csv
from common.rpc.sections import rpc_export_attendance

def export():
    print("Getting tutorial attendance...")

    raw = rpc_export_attendance(full=False)["custom"]["attendances"]
    c = csv.reader(raw)

    print("Saving tutorial attendance...")
    with open("data/tutorials.csv", "w") as f:
        f.write("Email,Tutorial Attendance (Total)\n")
        f.write(raw)
    print("Done.")


if __name__ == "__main__":
    export()

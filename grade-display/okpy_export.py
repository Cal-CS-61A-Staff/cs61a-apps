import requests, auth, sys

COURSE_CODE = "cs61a"
SEMESTER = "fa20"

def export():
    OK_SERVER = "https://okpy.org"
    ENDPOINT = "/api/v3/course/cal/{cc}/{sem}/grades".format(cc=COURSE_CODE, sem=SEMESTER)
    FILE_PATH = "data/okpy_grades.csv"

    access_token = auth.get_token()

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

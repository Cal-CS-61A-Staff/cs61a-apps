# Howamidoing

Howamidoing is a tool that displays and forecasts grades for lower-div EECS 
classes at UC Berkeley.

If you are a current student or staff, you can visit
[howamidoing.cs61a.org](https://howamidoing.cs61a.org) to see it in action!

## Features
**Students:**
- Authentication with okpy
- View grade breakdown per assignment
- Grade planning: test possible scores and view minimum score needed on final
  for specific grade boundaries

**Staff:**
- View histogram
- Export scores
- Import grades from CSV
- Edit configuration

## Setup

To develop, create a venv and install the python dependencies in
`server/requirements.txt`, run `yarn`, then run `yarn dev`. `yarn dev` will
concurrently run `python3 main.py` (backend) and `yarn start` (frontend).

## Uploading Grades
A `grades.csv` file can be uploaded to the server to update grades for students.
You can view an example
[here](https://github.com/Cal-CS-61A-Staff/cs61a-apps/blob/master/howamidoing/public/config/dummy_grade_data.csv).
`Name`, `Email`, `SID` fields are required (in that order), and the following
fields correspond to grades for each assignment.


## Editing Configuration
A `config.js` script can be uploaded to the server. You can view a sample config
[here](https://github.com/Cal-CS-61A-Staff/cs61a-apps/blob/master/howamidoing/public/config/config.js).
Here is some data that may be customized:

| Object      | Description |
| ----------- | ----------- |
| `BINS`      | List of numerical cutoffs (inclusive) corresponding to each grade |
| `GRADES`   | Name for each grade corresponding to each bin in `BINS`        |
| `COURSE_CODE` | String ID of the course |
| `WARNING` | Appears on the top of the page in the student view |
| `EXPLANATION` | Appears on the top right of the page in student view |
| `EXPLANATION_IS_LINK` | Set to `true` to make the explanation contents clickable |
| `ENABLE_PLANNING` | Set to `true` to allow students to use the grade planning feature |



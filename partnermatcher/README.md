# `partnermatcher`

This is an app that is used to calculate the optimal pairings for students 
looking for project partners, based on their response to several
partner-matching questions.

## Setup

To use the partner matching script, first create a form for students to fill out
with the following columns:

- Email Address
- What is 8am PT (Berkeley Time) in your time?
- How skillful a programmer do you consider yourself to be at this time?
- Are you taking CS 61A for a letter grade?
- What are three words that describe your interests?

Create a venv and install Python dependencies:

```bash
$ python3 -m venv env
$ env/bin/pip install -r requirements.txt
```

## Running the Script

Once the deadline to fill out the form has passed, export the results to
`partnermatcher/data.csv`. Then, update the spreadsheet location information
on lines 96 and 97. Make sure these sheets are shared with
`secure-links@ok-server.iam.gserviceaccount.com`.

To run the matching script and upload output to Google Sheets, run
`env/bin/python main.py`.
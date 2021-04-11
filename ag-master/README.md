# 61A Autograder

This is the communication layer between Okpy and the 61A Autograder Worker,
which grades students assignments and sends score back to Okpy. The worker code
is kept private for security reasons, but this only affects you if you choose
to use our workers and don't implement your own. If you wish to use ours, ask
a 61A Infrastructure TA for guidance.

## Setup

1. Clone the repo and switch into the `ag_master` directory.
2. Run `sicp venv` to create a virtual environment (`python3 -m venv env`) and
   install requirements (`env/bin/pip install -r requirements.txt`).
3. Run `env/bin/python main.py` to start the Autograder server. You may need to
   be logged into a `gcloud` account with access to the cs61a project in order
   to access cloud storage buckets, as local development is currently somewhat
   unsupported.

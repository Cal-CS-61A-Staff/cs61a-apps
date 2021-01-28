import os, zipfile, sys, requests, json
from functools import wraps

from flask import Flask, request, abort, session, send_file
from werkzeug.security import gen_salt

from common.oauth_client import create_oauth_client, get_user, is_logged_in
from common.rpc.auth import is_admin
from common.rpc.secrets import get_secret

from common.db import connect_db

app = Flask(__name__)
app.secret_key = "xyz"

create_oauth_client(app, "61a-autograder")

if not os.path.exists("./zips/cs61a"):
    os.makedirs("./zips/cs61a")

with connect_db() as db:
    db(
        """CREATE TABLE IF NOT EXISTS assignments (
    id varchar(128),
    name text,
    file text,
    command text
)
"""
    )

    db(
        """CREATE TABLE IF NOT EXISTS jobs (
    id varchar(128),
    assignment text,
    backup_id text,
    status text
)
"""
    )

def check_secret(func):
    @wraps(func)
    def wrapped():
        if request.headers.get("Authorization", None) == get_secret(secret_name="AG_UPLOAD_SECRET"):
            return func()
        abort(403)
    return wrapped


@app.route("/create_assignment", methods=["POST"])
@check_secret
def create_assignment():
    data = request.get_json()
    name = data["name"]
    file = data["filename"]
    command = data["command"]

    id = gen_salt(24)
    with connect_db() as db:
        existing = db("SELECT id, name FROM assignments WHERE name = %s", [name]).fetchone()
        if existing:
            db("UPDATE assignments SET file = %s, command = %s WHERE name = %s", [file, command, name])
            return dict(assign_id=existing[0])
        db("INSERT INTO assignments (id, name, file, command) VALUES (%s, %s, %s, %s)", [id, name, file, command])
        return dict(assign_id=id)
    

@app.route("/get_zip", methods=["POST"])
@check_secret
def get_zip():
    with connect_db() as db:
        assignment = db("SELECT file FROM assignments WHERE id=%s", [request.get_json()['assignment_id']]).fetchone()
    return send_file("zips/cs61a/" + assignment[0])

@app.route("/api/ok/v3/grade/batch", methods=["POST"])
def batch_grade():
    data = request.get_json()
    subms = data['subm_ids']
    assignment_id = data['assignment']
    if assignment_id == 'test':
        return 'OK'
    ok_token = data['access_token']

    with connect_db() as db:
        assignment = db("SELECT name, file, cmd FROM assignments WHERE id = %s", [assignment_id]).fetchone()
    if not assignment:
        abort(404, "Unknown Assignment")

    name, file, cmd = assignment
    batches = [subms[i:i + 100] for i in range(0, len(subms), 100)]

    return dict(jobs = [*trigger_jobs(assignment_id, name, cmd, batch, ok_token) for batch in batches])


def trigger_jobs(assignment, name, cmd, ids, ok_token):
    jobs = []
    with connect_db() as db:
        for id in ids:
            job_id = gen_salt(24)
            db("INSERT INTO jobs (id, assignment, backup_id, status) VALUES (%s, %s, %s, %s)", [job_id, assignment, id, "queued"])
            jobs.append(job_id)

        requests.post("https://ag-worker.cs61a.org/batch_grade", json=dict(assignment_id=assignment, assignment_name=name, command=cmd, jobs=jobs, backups=ids, access_token=ok_token), headers=dict(Authorization=get_secret("AG_WORKER_SECRET")))
    return jobs


@app.route("/results/<job_id>", methods=["GET"])
def get_results_for(job_id):
    with connect_db() as db:
        status = db("SELECT status FROM jobs WHERE id = %s", [job_id]).fetchone()
    if status in ("finished", "failed"):
        return status[0], 200
    return "Nope!", 202


@app.route("/results", methods=["POST"])
def get_results():
    def job_json(job_id):
        with connect_db() as db:
            status = db("SELECT status FROM jobs WHERE id = %s", [job_id]).fetchone()
        return {
            'status': status[0],
            'result': status[0],
        } if status else None

    return {
        job_id: job_json(job_id) for job_id in request.get_json()
    }
    
@app.route("/set_results", methods=["POST"])
@check_secret
def set_results():
    data = request.get_json()
    with connect_db() as db:
        db(
            "UPDATE jobs SET status = %s WHERE id = %s AND assignment = %s",
            [data['status'], data['job_id'], data['assignment_id']]
        )
    return dict(success=True)


@app.route("/upload_zip", methods=["POST"])
@check_secret
def upload_zip():
    file = request.files["upload"]
    file.save(f"zips/cs61a/{file.filename}")
    return dict(success=True)

@app.route("/")
def index():
    return "it works!"

if __name__ == "__main__":
    app.run()

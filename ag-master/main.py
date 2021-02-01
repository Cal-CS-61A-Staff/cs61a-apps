import os, requests, tempfile, sys
from functools import wraps

from flask import Flask, request, abort, send_file
from werkzeug.security import gen_salt

from google.cloud import storage

from common.oauth_client import create_oauth_client
from common.rpc.secrets import get_secret

from models import create_models, Course, Assignment, Job, db

app = Flask(__name__)
# create_oauth_client(app, "61a-autograder")

create_models(app)
db.init_app(app)
db.create_all(app=app)

MASTER_URL = "https://232.ag-master.pr.cs61a.org"
WORKER_URL = "https://232.ag-worker.pr.cs61a.org"
# WORKER_URL = "http://127.0.0.1:5001"

BUCKET = "ag-master.buckets.cs61a.org"

OKPY = "https://okpy.org"
# OKPY = "http://127.0.0.1:5002"
SUBM_ENDPOINT = OKPY + "/api/v3/backups"
SCORE_ENDPOINT = OKPY + "/api/v3/score/"


def check_secret(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        course = Course.query.filter_by(
            secret=request.headers.get("Authorization", None)
        ).first()
        if course:
            return func(course, *args, **kwargs)
        abort(403)

    return wrapped


def check_master(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        if request.headers.get("Authorization", None) == get_secret(
            secret_name="AG_MASTER_SECRET"
        ):
            return func(*args, **kwargs)
        abort(403)

    return wrapped


@app.route("/create_assignment", methods=["POST"])
@check_secret
def create_assignment(course):
    data = request.get_json()
    name = data["name"]
    file = data["filename"]
    command = data["command"]

    existing = Assignment.query.filter_by(name=name, course=course.secret).first()
    if existing:
        existing.file = file
        existing.command = command
        db.session.commit()
        return dict(assign_id=existing.ag_key)

    id = gen_salt(24)
    existing = Assignment(
        name=name, course=course.secret, file=file, command=command, ag_key=id
    )
    db.session.add(existing)
    db.session.commit()

    return dict(assign_id=id)


@app.route("/get_zip", methods=["POST"])
@check_secret
def get_zip(course):
    print(f"getting {request.get_json()['name']} for {course.name}")
    assignment = Assignment.query.filter_by(
        name=request.get_json()["name"], course=course.secret
    ).first()
    if assignment:
        bucket = storage.Client().get_bucket(BUCKET)
        blob = bucket.blob(f"zips/{course.name}-{course.semester}/{assignment.file}")
        with tempfile.NamedTemporaryFile() as temp:
            blob.download_to_filename(temp.name)
            return send_file(temp.name)
    abort(404)


@app.route("/api/ok/v3/grade/batch", methods=["POST"])
def batch_grade():
    data = request.get_json()
    subms = data["subm_ids"]
    assignment_id = data["assignment"]
    if assignment_id == "test":
        return "OK"
    ok_token = data["access_token"]

    assignment = Assignment.query.filter_by(ag_key=assignment_id).first()
    if not assignment:
        abort(404, "Unknown Assignment")

    jobs = [gen_salt(24) for _ in subms]

    objects = [
        Job(
            assignment=assignment.ag_key,
            backup=id,
            status="queued",
            job_key=job_id,
            access_token=ok_token,
        ) for id, job_id in zip(subms, jobs)
    ]
    db.session.bulk_save_objects(objects)
    db.session.commit()

    try:
        requests.post(
            f"{MASTER_URL}/trigger_jobs",
            json=dict(
                assignment_id=assignment_id,
                subms=subms,
                jobs=jobs,
                ok_token=ok_token,
            ),
            headers=dict(Authorization=get_secret(secret_name="AG_MASTER_SECRET")),
            timeout=1,
        )
    except requests.exceptions.ReadTimeout:
        pass

    return dict(jobs=jobs)


@app.route("/trigger_jobs", methods=["POST"])
@check_master
def trigger_jobs():
    data = request.get_json()
    assignment_id = data["assignment_id"]
    subms = data["subms"]
    jobs = data["jobs"]
    ok_token = data["ok_token"]

    assignment = Assignment.query.filter_by(ag_key=assignment_id).first()
    if not assignment:
        abort(404, "Unknown Assignment")

    subm_batches = [subms[i : i + 100] for i in range(0, len(subms), 100)]
    job_batches = [jobs[i : i + 100] for i in range(0, len(jobs), 100)]

    for subm_batch, job_batch in zip(subm_batches, job_batches):
        trigger_job_batch(assignment, subm_batch, job_batch, ok_token)
    return dict(success=True)


def trigger_job_batch(assignment, ids, jobs, ok_token):
    try:
        requests.post(
            f"{WORKER_URL}/batch_grade",
            json=dict(
                assignment_id=assignment.ag_key,
                assignment_name=assignment.name,
                command=assignment.command,
                jobs=jobs,
                backups=ids,
                course_key=assignment.course,
            ),
            headers=dict(Authorization=get_secret(secret_name="AG_WORKER_SECRET")),
            timeout=1,
        )
    except requests.exceptions.ReadTimeout:
        pass
    return jobs


@app.route("/send_score", methods=["POST"])
@check_secret
def send_score(course):
    data = request.get_json()
    payload = data["payload"]
    job = Job.query.filter_by(job_key=data["job_id"]).first()
    assignment = Assignment.query.filter_by(
        ag_key=job.assignment, course=course.secret
    )  # validates secret
    if job and assignment:
        requests.post(
            SCORE_ENDPOINT, data=payload, params=dict(access_token=job.access_token)
        )
    return dict(success=(job is not None))


@app.route("/get_submission", methods=["POST"])
@check_secret
def get_submission(course):
    data = request.get_json()
    id = data["id"]
    job = Job.query.filter_by(job_key=data["job_id"]).first()
    assignment = Assignment.query.filter_by(
        ag_key=job.assignment, course=course.secret
    )  # validates secret
    if job and assignment:
        r = requests.get(
            SUBM_ENDPOINT + "/" + str(id), params=dict(access_token=job.access_token)
        )
        print("requesting " + SUBM_ENDPOINT + "/" + str(id), file=sys.stderr)
        r.raise_for_status()
        return r.json()
    return dict(success=False)


@app.route("/results/<job_id>", methods=["GET"])
def get_results_for(job_id):
    job = Job.query.filter_by(job_key=job_id).first()
    if job and job.status in ("finished", "failed"):
        return job.status, 200
    return "Nope!", 202


@app.route("/results", methods=["POST"])
def get_results():
    job_ids = request.get_json()
    jobs = Job.query.filter(Job.job_key.in_(job_ids)).all()

    res = {job.job_key: dict(status=job.status, result=job.result) for job in jobs}
    for job in job_ids:
        if job not in res:
            res[job] = None

    return res


@app.route("/set_results", methods=["POST"])
@check_secret
def set_results(course):
    data = request.get_json()
    job = Job.query.filter_by(job_key=data["job_id"]).first()
    assignment = Assignment.query.filter_by(
        ag_key=job.assignment, course=course.secret
    )  # validates secret
    if job and assignment:
        job.status = data["status"]
        job.result = data["result"]
        db.session.commit()
    return dict(success=(job is not None))


@app.route("/upload_zip", methods=["POST"])
@check_secret
def upload_zip(course):
    file = request.files["upload"]
    bucket = storage.Client().get_bucket(BUCKET)
    blob = bucket.blob(f"zips/{course.name}-{course.semester}/{file.filename}")
    blob.upload_from_string(file.read(), content_type=file.content_type)
    return dict(success=True)


@app.route("/")
def index():
    return "it works!"


@app.route("/admin/courses")
@check_master
def course_list():
    courses = Course.query.all()
    return dict(
        success=True,
        courses=[
            {
                "name": c.name,
                "semester": c.semester,
            }
            for c in courses
        ],
    )


@app.route("/admin/courses/<semester>")
@check_master
def courses_in(semester):
    courses = Course.query.filter_by(semester=semester).all()
    return dict(
        success=True,
        courses=[
            {
                "name": c.name,
                "semester": c.semester,
            }
            for c in courses
        ],
    )


@app.route("/admin/<course>/<semester>")
@check_master
def course_info_admin(course, semester):
    course = Course.query.filter_by(name=course, semester=semester).first()
    if not course:
        abort(404)
    assignments = Assignment.query.filter_by(course=course.secret)
    return {
        "secret": course.secret,
        "assignments": [
            {
                "name": a.name,
                "file": a.file,
                "command": a.command,
                "ag_key": a.ag_key,
            }
            for a in assignments
        ],
    }


@app.route("/admin/create_course", methods=["POST"])
@check_master
def create_course():
    data = request.get_json()
    name = data["name"]
    sem = data["semester"]

    existing = Course.query.filter_by(name=name, semester=sem).first()
    if existing:
        return (
            "This course already exists. If you've misplaced your master key, contact a 61A admin!",
            400,
        )

    secret = gen_salt(24)
    db.session.add(Course(name=name, semester=sem, secret=secret))
    db.session.commit()

    os.makedirs(f"./zips/{name}-{sem}/")

    return dict(success=True, name=name, semester=sem, secret=secret)


@app.route("/course_info")
@check_secret
def course_info(course):
    assignments = Assignment.query.filter_by(course=course.secret)
    return {
        "assignments": [
            {
                "name": a.name,
                "file": a.file,
                "command": a.command,
                "ag_key": a.ag_key,
            }
            for a in assignments
        ]
    }


@app.route("/jobs/<job>")
@check_secret
def job_info(course, job):
    job = Job.query.filter_by(job_key=job).first()
    if not job:
        abort(404)

    assignment = Assignment.query.filter_by(ag_key=job.assignment).first()
    if not assignment or assignment.course != course.secret:
        abort(403)

    return {
        "assignment": assignment.name,
        "backup": job.backup,
        "status": job.status,
        "result": job.result,
    }


if __name__ == "__main__":
    app.run()

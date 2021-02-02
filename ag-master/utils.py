from flask import abort, request
from functools import wraps
from models import Course

from common.rpc.secrets import get_secret
from common.oauth_client import get_user, login, is_staff
from common.course_config import is_admin, is_admin_token

BUCKET = "ag-master.buckets.cs61a.org"

MASTER_URL = "https://232.ag-master.pr.cs61a.org"
WORKER_URL = "https://232.ag-worker.pr.cs61a.org"

OKPY = "https://okpy.org"
SUBM_ENDPOINT = OKPY + "/api/v3/backups"
SCORE_ENDPOINT = OKPY + "/api/v3/score/"

BATCH_SIZE = 100


def check_course_secret(func):
    @wraps(func)
    def wrapped(*args, course, **kwargs):
        course = Course.query.filter_by(secret=course).first()
        if course:
            return func(course, *args, **kwargs)
        raise PermissionError

    return wrapped


def check_master_secret(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        if request.headers.get("Authorization", None) == get_secret(
            secret_name="AG_MASTER_SECRET"
        ):
            return func(*args, **kwargs)
        abort(403)

    return wrapped


def admin_only_rpc(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        token = kwargs.pop("access_token", None)
        course = kwargs.pop("course", "cs61a")
        if (token and is_admin_token(access_token=token, course=course)) or (
            is_staff(course=course)
            and is_admin(email=get_user()["email"], course=course)
        ):
            semester = kwargs.pop("semester", "sp21")
            crs = Course.query.filter_by(name=course, semester=semester).first()
            if crs:
                return func(crs, *args, **kwargs)
            abort(404)
        return login()

    return wrapped


def admin_only(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        token = request.json.get("access_token", None)
        course = request.json.get("course", "cs61a")
        if (token and is_admin_token(access_token=token, course=course)) or (
            is_staff(course=course)
            and is_admin(email=get_user()["email"], course=course)
        ):
            semester = request.json.get("semester", "sp21")
            crs = Course.query.filter_by(name=course, semester=semester).first()
            if crs:
                return func(crs, *args, **kwargs)
            abort(404)
        return login()

    return wrapped


def superadmin_only(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        token = request.json.get("access_token", None)
        if (token and is_admin_token(access_token=token, course="cs61a")) or (
            is_staff(course="cs61a")
            and is_admin(email=get_user()["email"], course="cs61a")
        ):
            return func(*args, **kwargs)
        return login()

    return wrapped

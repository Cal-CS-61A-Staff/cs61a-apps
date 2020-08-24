from functools import wraps

from flask import session, request, redirect, abort

from common.db import connect_db
from common.oauth_client import get_user
from common.url_for import url_for

AUTHORIZED_ROLES = ["staff", "instructor", "grader"]


def is_staff(course):
    try:
        token = session.get("access_token") or request.cookies.get("access_token")
        if not token:
            return False

        email = get_user()["email"]
        with connect_db() as db:
            if course:
                admins = db(
                    "SELECT email FROM course_admins WHERE course=(%s)", [course]
                ).fetchall()
                admins = set(x[0] for x in admins)
                if admins:
                    if email in admins:
                        db(
                            "UPDATE course_admins SET name=(%s) WHERE email=(%s)",
                            [get_name(), email],
                        )
                        return True
                    else:
                        return False

        # otherwise, let anyone on staff access
        with connect_db() as db:
            if course is not None:
                [endpoint] = db(
                    "SELECT endpoint FROM courses WHERE course=(%s)", [course]
                ).fetchone()
            else:
                endpoint = None
        for participation in get_user()["participations"]:
            if participation["role"] not in AUTHORIZED_ROLES:
                continue
            if participation["course"]["offering"] != endpoint and endpoint is not None:
                continue
            return True
        return False
    except Exception as e:
        # fail safe!
        print(e)
        return False


def get_name():
    return get_user()["name"]


def get_email():
    return get_user()["email"]


def admin_oauth_secure(app):
    def decorator(route):
        @wraps(route)
        def wrapped(*args, **kwargs):
            assert "course" not in kwargs
            if not is_staff(MASTER_COURSE):
                return redirect(url_for("login"))
            return route(*args, **kwargs)

        return wrapped

    return decorator


def course_oauth_secure():
    def decorator(route):
        @wraps(route)
        def wrapped(*args, **kwargs):
            if not is_staff(kwargs["course"]):
                return redirect(url_for("login"))
            return route(*args, **kwargs)

        return wrapped

    return decorator


def oauth_secure():
    def decorator(route):
        @wraps(route)
        def wrapped(*args, **kwargs):
            if not is_staff(None):
                return redirect(url_for("login"))
            return route(*args, **kwargs)

        return wrapped

    return decorator


def key_secure(route):
    @wraps(route)
    def wrapped(**kwargs):
        kwargs.pop("client_name", None)  # legacy argument
        secret = kwargs.pop("secret")
        with connect_db() as db:
            ret_regular = db(
                "SELECT client_name, course FROM auth_keys WHERE auth_key = (%s)",
                [secret],
            ).fetchone()
            ret_super = db(
                "SELECT client_name FROM super_auth_keys WHERE auth_key = (%s)",
                [secret],
            ).fetchone()
            if ret_regular:
                client_name = ret_regular[0]
                course = ret_regular[1]
                db(
                    "UPDATE auth_keys SET unused = FALSE WHERE client_name=(%s)",
                    [client_name],
                )
                # the course might still be passed in, but should be ignored
                kwargs.pop("course", None)
            elif ret_super:
                client_name = ret_super[0]
                db(
                    "UPDATE super_auth_keys SET unused = FALSE WHERE client_name=(%s)",
                    [client_name],
                )
                course = kwargs.pop("course")
            else:
                abort(401)
        return route(**kwargs, course=course)

    return wrapped


MASTER_COURSE = "cs61a"

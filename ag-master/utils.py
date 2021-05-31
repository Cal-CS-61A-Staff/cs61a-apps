from functools import wraps

from common.course_config import is_admin, is_admin_token
from common.oauth_client import get_user, is_staff, login

BUCKET = "ag-master.buckets.cs61a.org"

SUBM_ENDPOINT = "/api/v3/backups"
SCORE_ENDPOINT = "/api/v3/score/"


def admin_only(func):
    """Require a user to either be logged into the UI, or so pass in an
    access token. Either way, the user must be an admin for the course they're
    attempting to access.

    :return: a function that takes in an ``access_token`` and a ``course``,
        along with the parameters passed into the original ``func``, which is
        called with all of the available arguments except ``access_token``
    """

    @wraps(func)
    def wrapped(*args, access_token=None, course="cs61a", **kwargs):
        token_good = access_token and is_admin_token(
            access_token=access_token, course=course
        )
        cookie_good = is_staff(course=course) and is_admin(
            email=get_user()["email"], course=course
        )
        if token_good or cookie_good:
            try:
                return func(*args, **kwargs, course=course)
            except PermissionError:
                pass
        if access_token:
            raise PermissionError
        else:
            return login()

    return wrapped


def super_admin_only(func):
    """Does almost the same thing as :func:`~docs.ag_master.utils.admin_only`,
    except the course must be ``cs61a``.

    :return: a function that takes in an ``access_token`` and a ``course``,
        along with the parameters passed into the original ``func``, which is
        called without ``access_token`` or ``course``
    """

    @wraps(func)
    @admin_only
    def wrapped(*args, course, **kwargs):
        if course != "cs61a":
            raise PermissionError
        return func(*args, **kwargs)

    return wrapped

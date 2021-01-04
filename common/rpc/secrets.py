from functools import wraps
from os import getenv

from flask import abort

from common.rpc.utils import cached, create_service, requires_master_secret
from common.course_config import is_admin_token

service = create_service(__name__)


def get_secret(*, secret_name):
    return getenv(secret_name) or get_secret_from_server(secret_name=secret_name)


@cached()
@requires_master_secret
@service.route("/api/get_secret")
def get_secret_from_server(*, secret_name):
    ...


@requires_master_secret
@service.route("/api/load_all_secrets")
def load_all_secrets(*, created_app_name):
    ...


def validates_master_secret(func):
    @wraps(func)
    def wrapped(
        *,
        master_secret=None,
        _sudo_token=None,
        _impersonate=None,
        _is_staging=False,
        **kwargs
    ):
        if master_secret:
            app, is_staging = validate_master_secret(master_secret=master_secret)
            return func(app=app, is_staging=is_staging, **kwargs)
        elif _sudo_token and is_admin_token(_sudo_token):
            return func(app=_impersonate, is_staging=_is_staging, **kwargs)

        raise PermissionError

    return wrapped


def only(allowed_app, *, allow_staging=False):
    def decorator(func):
        @wraps(func)
        def wrapped(master_secret, **kwargs):
            app, is_staging = validate_master_secret(master_secret=master_secret)
            allowed_apps = (
                [allowed_app] if isinstance(allowed_app, str) else allowed_app
            )
            if app not in allowed_apps:
                abort(403)
            if is_staging and not allow_staging:
                abort(403)
            return func(**kwargs)

        return wrapped

    return decorator


@cached()
@service.route("/api/validate_master_secret")
def validate_master_secret(*, master_secret):
    ...


@requires_master_secret
@service.route("/api/create_master_secret")
def create_master_secret(*, created_app_name):
    ...

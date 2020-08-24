from functools import wraps

from common.rpc.utils import cached, create_service, requires_master_secret

service = create_service(__name__)


@cached()
@requires_master_secret
@service.route("/api/get_secret")
def get_secret(*, secret_name):
    ...


def validates_master_secret(func):
    @wraps(func)
    def wrapped(*, master_secret, **kwargs):
        app, is_staging = validate_master_secret(master_secret=master_secret)
        return func(app=app, is_staging=is_staging, **kwargs)

    return wrapped


@cached()
@service.route("/api/validate_master_secret")
def validate_master_secret(*, master_secret):
    ...


@requires_master_secret
@service.route("/api/create_master_secret")
def create_master_secret(*, created_app_name):
    ...

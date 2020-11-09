from common.rpc.utils import create_service, requires_master_secret

service = create_service(__name__)


@requires_master_secret
@service.route("/api/index_piazza")
def index_piazza():
    ...


@requires_master_secret
@service.route("/api/clear_resources")
def clear_resources():
    ...


@requires_master_secret
@service.route("/api/upload_resources")
def upload_resources():
    ...

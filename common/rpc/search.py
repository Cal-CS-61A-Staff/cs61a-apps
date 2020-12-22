from common.rpc.utils import create_service, requires_master_secret

service = create_service(__name__)


@requires_master_secret
@service.route("/clear/piazza")
def clear_piazza():
    ...


@requires_master_secret
@service.route("/insert/piazza")
def insert_piazza(*, posts):
    ...


@requires_master_secret
@service.route("/clear/resources")
def clear_resources():
    ...


@requires_master_secret
@service.route("/insert/resources")
def insert_resources(*, resources):
    ...


@service.route("/query")
def query(*, piazza_params, resource_params):
    ...

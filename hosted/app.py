import os
from dna import DNA
from flask import Flask, abort
from functools import wraps

from common.rpc.hosted import (
    add_domain,
    delete,
    list_apps,
    new,
    run,
    stop,
    service_log,
    container_log,
)
from common.rpc.secrets import only
from common.shell_utils import sh
from common.oauth_client import (
    create_oauth_client,
    is_logged_in,
    is_staff,
    login,
)

CERTBOT_ARGS = [
    "--dns-google",
    "--dns-google-propagation-seconds",
    "180",
]

app = Flask(__name__)
dna = DNA(
    "hosted",
    cb_args=CERTBOT_ARGS,
)

if not os.path.exists("data"):
    os.makedirs("data")

if not os.path.exists("data/saves"):
    os.makedirs("data/saves")

sh("chmod", "666", f"{os.getcwd()}/dna.sock")


@list_apps.bind(app)
@only("buildserver")
def list_apps():
    return {
        service.name: {
            "image": service.image,
            "domains": [d.url for d in service.domains],
        }
        for service in dna.services
    }


@new.bind(app)
@only("buildserver")
def new(img, name=None, env={}):
    name = name if name else img.split("/")[-1]

    [
        _ for _ in dna.pull_image(img)
    ]  # temporary fix until DNA supports pulling without streaming

    if "ENV" not in env:
        env["ENV"] = "prod"
    if "PORT" not in env:
        env["PORT"] = 8001

    save = f"{os.getcwd()}/data/saves/{name}"
    if not os.path.exists(save):
        os.makedirs(save)

    volumes = {
        save: {
            "bind": "/save",
            "mode": "rw",
        },
    }

    dna.run_deploy(
        name,
        img,
        "8001",
        environment=env,
        volumes=volumes,
    )

    return dict(success=True)


@delete.bind(app)
@only("buildserver")
def delete(name):
    dna.delete_service(name)
    return dict(success=True)


@add_domain.bind(app)
@only(["buildserver", "sandbox"])
def add_domain(name, domain, force_wildcard=False, force_provision=False):
    return dict(success=dna.add_domain(name, domain, force_wildcard, force_provision))


@service_log.bind(app)
@only("logs")
def service_log():
    logs = sh("journalctl", "-u", "dockerapi", "-n", "100", quiet=True).decode("utf-8")
    return dict(success=True, logs=logs)


@container_log.bind(app)
@only("logs")
def container_log(name):
    return dict(success=True, logs=dna.docker_logs(name))


def check_auth(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        if not is_logged_in():
            return login()
        if not is_staff("cs61a"):
            abort(401)
        return func(*args, **kwargs)

    return wrapped


create_oauth_client(app, "hosted-apps")

dna_api = dna.create_api_client(precheck=check_auth)
app.register_blueprint(dna_api, url_prefix="/api")

# PR Proxy Setup
from dna.utils import Certbot
from dna.utils.nginx_utils import Server, Location
from common.rpc.hosted import create_pr_subdomain

proxy_cb = Certbot(CERTBOT_ARGS + ["-i", "nginx"])
pr_confs = f"{os.getcwd()}/data/pr_proxy"

if not os.path.exists(pr_confs):
    os.makedirs(pr_confs)

if not os.path.exists(f"/etc/nginx/conf.d/hosted_pr_proxy.conf"):
    with open(f"/etc/nginx/conf.d/hosted_pr_proxy.conf", "w") as f:
        f.write(f"include {pr_confs}/*.conf;")


@create_pr_subdomain.bind(app)
@only("buildserver")
def create_pr_subdomain(app, pr_number, pr_host):
    if os.path.exists(f"{pr_confs}/{pr_number}.{app}.pr.cs61a.org.conf"):
        return dict(success=True)

    nginx_config = Server(
        Location(
            "/",
            proxy_pass=f"https://{pr_host}/",
            proxy_read_timeout="1800",
            proxy_connect_timeout="1800",
            proxy_send_timeout="1800",
            send_timeout="1800",
            **{
                "proxy_set_header Host": pr_host,
                "proxy_set_header X-Forwarded-For-Host": f"{pr_number}.{app}.pr.cs61a.org",
            },
        ),
        server_name=f"{pr_number}.{app}.pr.cs61a.org",
        listen="80",
    )

    with open(f"{pr_confs}/{pr_number}.{app}.pr.cs61a.org.conf", "w") as f:
        f.write(str(nginx_config))
    sh("nginx", "-s", "reload")

    cert = proxy_cb.cert_else_false(f"*.{app}.pr.cs61a.org", force_exact=True)
    if not cert:
        proxy_cb.run_bot(domains=[f"*.{app}.pr.cs61a.org"], args=["certonly"])
        cert = proxy_cb.cert_else_false(f"*.{app}.pr.cs61a.org", force_exact=True)
    proxy_cb.attach_cert(cert, f"{pr_number}.{app}.pr.cs61a.org")

    return dict(success=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0")

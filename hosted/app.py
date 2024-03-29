import os, sys
from dna import DNA
from flask import Flask
from functools import wraps

from common.rpc.hosted import (
    add_domain,
    delete,
    list_apps,
    new,
    service_log,
    container_log,
)
from common.rpc.secrets import only
from common.shell_utils import sh
from common.oauth_client import (
    create_oauth_client,
    is_staff,
    login,
    get_user,
)
from common.rpc.auth import is_admin
from common.rpc.slack import post_message

CERTBOT_ARGS = [
    "--dns-google",
    "--dns-google-propagation-seconds",
    "180",
]

is_sphinx = "sphinx" in sys.argv[0]

app = Flask(__name__)

if not is_sphinx:
    dna = DNA(
        "hosted",
        cb_args=CERTBOT_ARGS,
    )

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

    shared = f"{os.getcwd()}/data/shared"
    if not os.path.exists(shared):
        os.makedirs(shared)

    volumes = {
        save: {
            "bind": "/save",
            "mode": "rw",
        },
        shared: {
            "bind": "/shared",
            "mode": "ro",
        },
    }

    dna.run_deploy(
        name,
        img,
        "8001",
        environment=env,
        volumes=volumes,
        hostname=name,
    )
    dna.add_domain(
        name,
        f"{name}.hosted.cs61a.org",
    )

    return dict(success=True)


@delete.bind(app)
@only("buildserver")
def delete(name):
    dna.delete_service(name)
    return dict(success=True)


@add_domain.bind(app)
@only(["buildserver", "sandbox"], allow_staging=True)
def add_domain(
    name, domain, force_wildcard=False, force_provision=False, proxy_set_header={}
):
    return dict(
        success=dna.add_domain(
            name, domain, force_wildcard, force_provision, proxy_set_header
        )
    )


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
    """Takes in a function, and returns a wrapper of that function.
    The wrapper will request user authentication (as staff) if needed.
    Otherwise, it will execute the function as normal.

    :param func: function to wrap
    :type func: func

    :return: wrapper function that requests authentication as needed
    """

    @wraps(func)
    def wrapped(*args, **kwargs):
        if not (is_staff("cs61a") and is_admin(email=get_user()["email"])):
            return login()
        return func(*args, **kwargs)

    return wrapped


if not is_sphinx:
    create_oauth_client(app, "hosted-apps")

    dna_api = dna.create_api_client(precheck=check_auth)
    app.register_blueprint(dna_api, url_prefix="/dna")

    dna_logs = dna.create_logs_client(precheck=check_auth)
    app.register_blueprint(dna_logs, url_prefix="/logs")

# PR Proxy Setup
from dna.utils import Certbot
from dna.utils.nginx_utils import Server, Location
from common.rpc.hosted import create_pr_subdomain

proxy_cb = Certbot(CERTBOT_ARGS + ["-i", "nginx"])
pr_confs = f"{os.getcwd()}/data/pr_proxy"

if not is_sphinx:
    if not os.path.exists(pr_confs):
        os.makedirs(pr_confs)

    if not os.path.exists(f"/etc/nginx/conf.d/hosted_pr_proxy.conf"):
        with open(f"/etc/nginx/conf.d/hosted_pr_proxy.conf", "w") as f:
            f.write(f"include {pr_confs}/*.conf;")


@create_pr_subdomain.bind(app)
@only("buildserver")
def create_pr_subdomain(app, pr_number, pr_host):
    target_domain = f"{pr_number}.{app}.pr.cs61a.org"
    conf_path = f"{pr_confs}/{target_domain}.conf"
    expected_cert_name = f"*.{app}.pr.cs61a.org"

    nginx_config = Server(
        Location(
            "/",
            proxy_pass=f"https://{pr_host}/",
            proxy_read_timeout="1800",
            proxy_connect_timeout="1800",
            proxy_send_timeout="1800",
            send_timeout="1800",
            proxy_set_header={
                "Host": pr_host,
                "X-Forwarded-For-Host": target_domain,
            },
        ),
        server_name=target_domain,
        listen="80",
    )

    if not os.path.exists(conf_path):
        with open(conf_path, "w") as f:
            f.write(str(nginx_config))
        sh("nginx", "-s", "reload")

    cert = proxy_cb.cert_else_false(expected_cert_name, force_exact=True)
    for _ in range(2):
        if cert:
            break
        proxy_cb.run_bot(domains=[expected_cert_name], args=["certonly"])
        cert = proxy_cb.cert_else_false(expected_cert_name, force_exact=True)

    if not cert:
        error = f"Hosted Apps failed to sign a certificate for {expected_cert_name}!"
        post_message(message=error, channel="infra")
        return dict(success=False, reason=error)

    proxy_cb.attach_cert(cert, target_domain)
    return dict(success=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0")

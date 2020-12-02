import docker
from flask import Flask

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
from utils import *

app = Flask(__name__)
client = docker.from_env()

if not os.path.exists("data"):
    os.makedirs("data")


@list_apps.bind(app)
@only("buildserver")
def list_apps():
    containers = client.containers.list(all=True)
    info = {}
    apps = get_config()
    for c in containers:
        info[c.name] = {
            "running": c.status == "running",
            "image": c.image.tags[0] if c.image.tags else c.image.short_id[7:],
            "domains": apps[c.name]["domains"],
        }
    return info


@new.bind(app)
@only("buildserver")
def new(img, name=None, env={}):
    client.images.pull(img)

    if name is None:
        name = img.split("/")[-1]

    apps = get_config()

    if name in apps:
        for c in client.containers.list(all=True):
            if c.name == name:
                if c.status == "running":
                    c.kill()
                c.remove()
                break
        port = apps[name]["port"]
    else:
        port = get_empty_port()
        configure(name, port)

    if "ENV" not in env:
        env["ENV"] = "prod"
    if "PORT" not in env:
        env["PORT"] = 8001

    volumes = {
        f"{os.getcwd()}/data/saves/{name}": {
            "bind": "/save",
            "mode": "rw",
        },
    }

    client.containers.run(
        img,
        detach=True,
        environment=env,
        ports={int(env["PORT"]): port},
        volumes=volumes,
        name=name,
    )

    return f"Running on {name}.hosted.cs61a.org!"


@stop.bind(app)
@only("buildserver")
def stop(name):
    apps = get_config()

    if name in apps:
        for c in client.containers.list():
            if c.name == name:
                c.kill()
                return dict(success=True)

    return dict(
        success=False, reason="That container doesn't exist, or is not running."
    )


@run.bind(app)
@only("buildserver")
def run(name):
    apps = get_config()

    if name in apps:
        for c in client.containers.list():
            if c.name == name:
                return dict(success=False, reason="That container is already running.")
    else:
        return dict(success=False, reason="That container doesn't exist.")

    client.containers.get(name).start()
    return dict(success=True)


@delete.bind(app)
@only("buildserver")
def delete(name):
    apps = get_config()

    if name in apps:
        for c in client.containers.list(all=True):
            if c.name == name:
                if c.status == "running":
                    c.kill()
                c.remove()
                break
        deconfigure(name)
        return dict(success=True)
    else:
        return dict(success=False, reason="That container doesn't exist.")


@add_domain.bind(app)
@only(["buildserver", "sandbox"])
def add_domain(name, domain, force=False):
    apps = get_config()

    if not force:
        for other_app in apps:
            if domain in apps[other_app]["domains"]:
                return dict(
                    success=False,
                    reason=f"That domain is already bound to {other_app}. Use 'force=True' to overwrite.",
                )

    if name in apps:
        write_nginx(domain, apps[name]["port"])
        redirect(domain, name)
        return dict(success=True)

    return dict(success=False, reason="That container doesn't exist.")


@service_log.bind(app)
@only("logs")
def service_log():
    logs = sh("journalctl", "-u", "dockerapi", "-n", "100", quiet=True).decode("utf-8")
    return dict(success=True, logs=logs)


@container_log.bind(app)
@only("logs")
def container_log(name):
    apps = get_config()

    if name in apps:
        c = client.containers.get(name)
        logs = c.logs(tail=100, timestamps=True).decode("utf-8")
        return dict(success=True, logs=logs)
    else:
        return dict(success=False, reason="That container doesn't exist.")


if __name__ == "__main__":
    app.run(host="0.0.0.0")

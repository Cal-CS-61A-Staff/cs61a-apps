from flask import Flask, request, abort, jsonify
from utils import *
import docker, os

app = Flask(__name__)
client = docker.from_env()


@app.route("/", methods=["GET"])
def list_apps():
    containers = client.containers.list(all=True)
    info = {}
    apps = get_config()
    for c in containers:
        info[c.name] = {
            "running": c.status == "running",
            "image": c.image.tags[0],
            "domains": apps[c.name]["domains"],
        }
    return jsonify(info)


@app.route("/new", methods=["POST"])
def new():
    params = request.json
    secret = params.get("secret")
    if secret != os.environ.get("DEPLOY_KEY"):
        abort(403)

    if not "image" in params:
        abort(400)

    img = params.get("image")
    client.images.pull(img)

    if "name" in params:
        app_name = params.get("name")
    else:
        app_name = img.split("/")[-1]
    apps = get_config()

    if app_name in apps:
        for c in client.containers.list(all=True):
            if c.name == app_name:
                if c.status == "running":
                    c.kill()
                c.remove()
                break
        port = apps[app_name]["port"]
    else:
        port = get_empty_port()
        configure(app_name, port)

    env = {}
    if "env" in params:
        for key in params.get("env"):
            env[key] = params.get("env").get(key)

    if "ENV" not in env:
        env["ENV"] = "prod"
    if "PORT" not in env:
        env["PORT"] = 8001

    volumes = {
        f"{os.environ.get('HOME')}/docker-api/saves/{app_name}": {
            "bind": "/save",
            "mode": "rw",
        },
    }

    app = client.containers.run(
        img,
        detach=True,
        environment=env,
        ports={int(env["PORT"]): port},
        volumes=volumes,
        name=app_name,
    )

    return f"Running on {app_name}.hosted.cs61a.org!"


@app.route("/stop", methods=["POST"])
def stop():
    params = request.json
    secret = params.get("secret")
    if secret != os.environ.get("DEPLOY_KEY"):
        abort(403)

    if not "name" in params:
        abort(400)

    app_name = params.get("name")
    apps = get_config()

    if app_name in apps:
        for c in client.containers.list():
            if c.name == app_name:
                c.kill()
                return jsonify(success=True)

    return jsonify(
        success=False, reason="That container doesn't exist, or is not running."
    )


@app.route("/run", methods=["POST"])
def run():
    params = request.json
    secret = params.get("secret")
    if secret != os.environ.get("DEPLOY_KEY"):
        abort(403)

    if not "name" in params:
        abort(400)

    app_name = params.get("name")
    apps = get_config()

    if app_name in apps:
        for c in client.containers.list():
            if c.name == app_name:
                return jsonify(
                    success=False, reason="That container is already running."
                )
    else:
        return jsonify(success=False, reason="That container doesn't exist.")

    client.containers.get(app_name).start()
    return jsonify(success=True)


@app.route("/delete", methods=["POST"])
def delete():
    params = request.json
    secret = params.get("secret")
    if secret != os.environ.get("DEPLOY_KEY"):
        abort(403)

    if "name" not in params:
        abort(400)

    app_name = params.get("name")
    apps = get_config()

    if app_name in apps:
        for c in client.containers.list(all=True):
            if c.name == app_name:
                if c.status == "running":
                    c.kill()
                c.remove()
                break
        deconfigure(app_name)
        return jsonify(success=True)
    else:
        return jsonify(success=False, reason="That container doesn't exist.")


@app.route("/add_domain", methods=["POST"])
def add_domain():
    params = request.json
    secret = params.get("secret")
    if secret != os.environ.get("DEPLOY_KEY"):
        abort(403)

    if not "name" in params or not "domain" in params:
        abort(400)

    app_name = params.get("name")
    apps = get_config()

    domain = params.get("domain")

    if "force" not in params or not params.get("force"):
        for other_app in apps:
            if domain in apps[other_app]["domains"]:
                return jsonify(
                    success=False,
                    reason=f"That domain is already bound to {other_app}. Use 'force=True' to overwrite.",
                )

    if app_name in apps:
        write_nginx(domain, apps[app_name]["port"])
        redirect(domain, app_name)
        return jsonify(success=True)

    return jsonify(success=False, reason="That container doesn't exist.")


if __name__ == "__main__":
    app.run(host="0.0.0.0")

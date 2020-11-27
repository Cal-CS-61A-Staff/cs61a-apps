import socket, json, subprocess, os, shutil

NGINX_ENABLED = "/home/vs/docker-api/nginx-confs"
NGINX_TEMPLATE = """
server {
    server_name {domain};
    location / {
        include proxy_params;
        proxy_pass http://127.0.0.1:{port};
    }
}
"""


def delete_nginx(app_name):
    apps = get_config()
    for domain in apps[app_name]["domains"]:
        os.remove(f"{NGINX_ENABLED}/{domain}")
        process = subprocess.Popen(
            ["sudo", "certbot", "delete", "--cert-name", domain],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        _, _ = process.communicate()

    process = subprocess.Popen(
        ["sudo", "nginx", "-s", "reload"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _, _ = process.communicate()


def write_nginx(domain, port):
    contents = NGINX_TEMPLATE.replace("{domain}", domain).replace("{port}", str(port))
    with open(f"{NGINX_ENABLED}/{domain}", "w") as a:
        a.write(contents)
    process = subprocess.Popen(
        ["sudo", "nginx", "-s", "reload"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _, _ = process.communicate()
    process = subprocess.Popen(
        ["sudo", "certbot", "--nginx", "-d", domain, "--non-interactive"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _, _ = process.communicate()


def get_empty_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def make_save(app_name):
    if not os.path.exists(f"/home/vs/docker-api/saves/{app_name}"):
        os.makedirs(f"/home/vs/docker-api/saves/{app_name}")


def del_save(app_name):
    shutil.rmtree(f"/home/vs/docker-api/saves/{app_name}")


CONFIG = "config.json"


def get_config():
    with open(CONFIG) as f:
        return json.load(f)


def save_config(apps):
    with open(CONFIG, "w") as f:
        json.dump(apps, f)


def redirect(domain, app_name):
    apps = get_config()
    apps[app_name]["domains"].append(domain)
    with open(CONFIG, "w") as f:
        json.dump(apps, f)


def configure(app_name, port):
    make_save(app_name)

    apps = get_config()
    apps[app_name] = {"port": port, "domains": [f"{app_name}.hosted.cs61a.org"]}
    save_config(apps)
    write_nginx(f"{app_name}.hosted.cs61a.org", port)


def deconfigure(app_name):
    delete_nginx(app_name)
    del_save(app_name)

    apps = get_config()
    del apps[app_name]
    save_config(apps)

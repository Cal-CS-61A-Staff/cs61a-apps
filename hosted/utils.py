import json
import os
import shutil
import socket

from common.shell_utils import sh

CONFIG = f"{os.getcwd()}/data/config.json"
NGINX_ENABLED = f"{os.getcwd()}/data/nginx-confs"
NGINX_TEMPLATE = """
server {
    server_name {domain};
    location / {
        include proxy_params;
        proxy_pass http://127.0.0.1:{port};
    }
{ssl}
}
"""
NGINX_HOSTED_SSL = """
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/hosted.cs61a.org-0001/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/hosted.cs61a.org-0001/privkey.pem;

    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
"""

if not os.path.exists(NGINX_ENABLED):
    os.makedirs(NGINX_ENABLED)


def delete_nginx(app_name):
    apps = get_config()
    for domain in apps[app_name]["domains"]:
        os.remove(f"{NGINX_ENABLED}/{domain}")
        if not domain.endswith(".hosted.cs61a.org"):
            sh("sudo", "certbot", "delete", "--cert-name", domain)

    sh("sudo", "nginx", "-s", "reload")


def write_nginx(domain, port):
    contents = NGINX_TEMPLATE.replace("{domain}", domain).replace("{port}", str(port))
    contents = contents.replace(
        "{ssl}", NGINX_HOSTED_SSL if domain.endswith(".hosted.cs61a.org") else ""
    )
    with open(f"{NGINX_ENABLED}/{domain}", "w") as a:
        a.write(contents)
    sh("sudo", "nginx", "-s", "reload")
    if not domain.endswith(".hosted.cs61a.org"):
        sh("sudo", "certbot", "--nginx", "-d", domain, "--non-interactive")


def get_empty_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def make_save(app_name):
    if not os.path.exists(f"{os.getcwd()}/data/saves/{app_name}"):
        os.makedirs(f"{os.getcwd()}/data/saves/{app_name}")


def del_save(app_name):
    shutil.rmtree(f"{os.getcwd()}/data/saves/{app_name}")


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

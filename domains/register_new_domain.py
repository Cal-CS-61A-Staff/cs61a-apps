import hmac
import os
import subprocess

from flask import Flask, abort, request

app = Flask(__name__)


SECRET = os.getenv("SECRET")


# note: this can't be made a dependency, because pr_proxy does not use the standard build system
def sh(*args):
    subprocess.run(args).check_returncode()


@app.route("/create_domain", methods=["POST"])
def create_domain():
    secret = request.json["secret"]
    if not hmac.compare_digest(secret, SECRET):
        abort(403)
    domain = request.json["domain"]
    app = request.json["app"]
    conf = f"{domain}_autoconf.conf"
    existing_domains = os.listdir("/etc/nginx/conf.d")
    for existing_domain in existing_domains:
        if existing_domain == conf:
            return ""

    with open(f"/etc/nginx/conf.d/{conf}", "w+") as f:
        f.write(
            f"""
    server {{
      listen 443 ssl;
      server_name {app}.cs61a.org;
      location / {{
        proxy_pass https://{app}.cs61a.org/;
        proxy_set_header Host {app}.cs61a.org;
        proxy_set_header X-Forwarded-For-Host {domain};
        proxy_read_timeout 1800;
        proxy_connect_timeout 1800;
        proxy_send_timeout 1800;
        send_timeout 1800;
      }}
    }}"""
        )

    sh("certbot", "--nginx", "-d", domain, "--non-interactive")
    return ""  # certbot will automatically restart nginx

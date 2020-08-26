import hmac
import os
import subprocess

from flask import Flask, abort, request

app = Flask(__name__)


# note: this can't be made a dependency, because pr_proxy does not use the standard build system
def sh(*args):
    subprocess.run(args).check_returncode()


@app.route("/create_subdomain", methods=["POST"])
def create_subdomain():
    secret = request.json["secret"]
    SECRET = os.getenv("SECRET")
    if not hmac.compare_digest(secret, SECRET):
        abort(403)
    app = request.json["app"]
    pr_number = request.json["pr_number"]
    pr_host = request.json["pr_host"]
    conf = f"{app}_DONOTNAMEpullrequest{pr_number}_autoconf.conf"
    existing_apps = os.listdir("/etc/nginx/conf.d")
    cert_exists = False
    for existing_app in existing_apps:
        if existing_app == conf:
            return ""
        if existing_app.split("_DONOTNAMEpullrequest")[0] == app:
            cert_exists = True
    if not cert_exists:
        # add flag to record existence
        with open(f"/etc/nginx/conf.d/{conf}DONOTUSE", "w+") as f:
            f.write("# temp")
        # create certificate
        sh(
            "certbot",
            "certonly",
            "--dns-google",
            "-d",
            f"*.{app}.pr.cs61a.org",
            "--non-interactive",
            "--dns-google-propagation-seconds",
            "120",
        )
        return ""  # buildserver will call it again to restart nginx

    with open(f"/etc/nginx/conf.d/{conf}", "w+") as f:
        f.write(
            f"""
server {{
  listen 443 ssl;
  server_name {pr_number}.{app}.pr.cs61a.org;
  ssl_certificate /etc/letsencrypt/live/{app}.pr.cs61a.org/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/{app}.pr.cs61a.org/privkey.pem;
  include /etc/letsencrypt/options-ssl-nginx.conf;
  ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
  location / {{
    proxy_pass https://{pr_host}/;
    proxy_set_header Host {pr_host};
    proxy_set_header X-Forwarded-For-Host {pr_number}.{app}.pr.cs61a.org;
    proxy_read_timeout 1800;
    proxy_connect_timeout 1800;
    proxy_send_timeout 1800;
    send_timeout 1800;
  }}
}}"""
        )

    sh("systemctl", "restart", "nginx")

    return ""

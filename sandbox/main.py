import subprocess, os, socket
from utils import Server, Location
from common.shell_utils import sh
from common.rpc.secrets import get_secret

HOSTNAME = os.environ.get("HOSTNAME", "cs61a.org")
NGINX_PORT = os.environ.get("PORT", "8001")


def main():
    """Start the Sandbox and IDE servers."""
    sh("nginx")

    sandbox_port = get_open_port()
    sb = subprocess.Popen(
        ["gunicorn", "-b", f":{sandbox_port}", "-w", "4", "sandbox:app", "-t", "3000"],
        env=os.environ,
    )
    proxy(f"sb.{HOSTNAME} *.sb.{HOSTNAME}", sandbox_port, f"sb.{HOSTNAME}")
    proxy(f"*.sb.pr.{HOSTNAME}", sandbox_port, f"sb.pr.{HOSTNAME}")

    ide_port = get_open_port()
    ide = subprocess.Popen(
        ["gunicorn", "-b", f":{ide_port}", "-w", "4", "ide:app", "-t", "3000"],
        env=os.environ,
    )
    proxy(f"ide.{HOSTNAME}", ide_port, f"ide.{HOSTNAME}")
    proxy(f"*.ide.pr.{HOSTNAME}", ide_port, f"ide.pr.{HOSTNAME}")

    sh("nginx", "-s", "reload")

    ide.communicate()  # make sure docker doesn't close this container


def get_open_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))

    s.listen(1)
    port = s.getsockname()[1]

    s.close()
    return port


def proxy(domain, port, fn):
    conf = Server(
        Location(
            "/",
            include="proxy_params",
            proxy_pass=f"http://127.0.0.1:{port}",
        ),
        listen=NGINX_PORT,
        server_name=domain,
    )

    with open(f"/etc/nginx/sites-enabled/{fn}", "w") as f:
        f.write(str(conf))


if __name__ == "__main__":
    main()

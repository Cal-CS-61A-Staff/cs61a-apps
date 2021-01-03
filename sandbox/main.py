import subprocess, os, socket
from nginx_utils import Server, Location
from common.shell_utils import sh

HOSTNAME = os.environ.get("HOSTNAME", "cs61a.org")


def main():
    """Start the Sandbox and IDE servers."""
    nginx_port = os.environ["PORT"]
    sh("nginx")

    sandbox_port = get_open_port()
    subprocess.Popen(
        ["gunicorn", "-b", f":{sandbox_port}", "-w", "4", "sandbox:app", "-t", "3000"]
    )
    proxy(f"sb.{HOSTNAME} *.sb.{HOSTNAME}", sandbox_port, f"sb.{HOSTNAME}")

    ide_port = get_open_port()
    subprocess.Popen(
        ["gunicorn", "-b", f":{ide_port}", "-w", "4", "ide:app", "-t", "3000"],
        env=dict(os.environ, IDE_PORT=ide_port),
    )
    proxy(f"ide.{HOSTNAME}", ide_port, f"ide.{HOSTNAME}")

    sh("nginx", "-s", "reload")


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
        listen="8001",
        server_name=domain,
    )

    with open(f"/etc/nginx/sites-enabled/{fn}", "w") as f:
        f.write(str(conf))


if __name__ == "__main__":
    main()

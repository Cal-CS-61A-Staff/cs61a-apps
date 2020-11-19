## PR_Proxy

This is the _only_ service that is not managed by the `buildserver`. It is used to proxy PR subdomains (like <https://1.oh.pr.cs61a.org>) to the Cloud Run instances created by the `buildserver`.

The reason we can't use Cloud Run instances directly is because new subdomains take between 15 minutes and 24 hours to have TLS setup, which can be an issue when running smoke tests / manual testing.

Instead, we deploy PRs to their default Cloud Run domains, and `pr_proxy` hosts an nginx reverse proxy pointing to those domains from the nice looking ones.

We have a DNS `A` record from `*.pr.cs61a.org` to the IP address `34.94.235.143` where `pr_proxy` lives. Then, the nginx config is dynamically updated by `register_pr_build.py` (called `main.py` on the GCP instance) in response to requests sent from the `buildserver` on a PR build.

The secret is hardcoded in the `main.py` file on the server, and must be kept in sync with `buildserver/PR_PROXY_SECRET` in `secrets`, otherwise new PR builds will not work.

The GCP instance running `pr_proxy` is currently known as `staging-proxy` in the `us-west2-a` zone on the `cs61a` GCP account - it should basically be the smallest GCP instance possible, since it doesn't do very much. On boot, `gunicorn` will automatically start, and you might have to run `sudo systemctl start nginx` to start it up, thoughh that should also automatically run on boot.

Please _do not_ try to run any production service through `pr_proxy` - as it is a single VM, it has low reliability (~99.5%) relative to the Cloud Run / Cloud SQL services that run everything else (~99.95%). If you want to change the build process, you'll want to modify `buildserver`, almost certainly not `pr_proxy`.

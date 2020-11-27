# Hosted Docker API

This is 61A's internal Docker API implementation, similar to [Dokku](https://github.com/dokku/dokku) but more efficient and straightforward enough for our needs.

## Setup
To use this tool, you'll need to set up `nginx`, `docker`, and the `systemd` service.

1. Install `nginx` and `docker` for your distribution. If you wish to use SSL, install `certbot` as well.
2. Clone this repo. **For the remainder of this guide, we will refer to your cloned `hosted` directory as `$hosted`.** Make sure to replace `$hosted` with the absolute path to your cloned `hosted` directory.
3. Make sure your user has access to the `docker` CLI without `sudo`. Also make sure that your user can run `nginx` commands with `sudo` without a password.

### Python Setup
4. `cd` into `$hosted` and run `python3 -m venv env`. This will create the virtual environment that the `systemd` service will use.
5. Run `source env/bin/activate` to activate the environment, then run `pip install -r requirements` to install Python dependencies. Feel free to `deactivate` once this is done -- you will only need to activate this environment to run the app manually. The `systemd` service will activate it in its own environment automatically.

### `nginx` Setup
6. Edit `/etc/nginx/nginx.conf`. Under "Virtual Host Configs" at the bottom of `http`, add the line `include $hosted/nginx-confs/*;`.
7. Create an `nginx` config for this tool. See below for details on how to write the config file. Then, copy this file into `/etc/nginx/sites-available/`. To enable the new configuration, `cd` to `/etc/nginx/sites-enabled/` and run `ln -s ../sites-available/<config> <config>`. Replace `<config>` with the full name of the config file.
8. To use SSL, run `sudo certbot --nginx -d <url>` to install a Let's Encrypt certificate. Replace `<url>` with the fully-qualified URL (minus the protocol) to your service.
9. Run `sudo nginx -s reload` to read the new configurations.

Use the following skeleton for your config file. Replace `{url}` with the fully-qualified URL (minus the protocol) to your service.

```
server {
	server_name {url};

	location / {
		include proxy_params;
		proxy_pass http://unix:$hosted/api.sock;
	}
}
```

### `systemd` Setup
10. Create the `systemd` service. See below for details on how to write the `.service` file. Then, copy this file into `/etc/systemd/system/`. To start the service once, run `sudo systemctl start <servicename>`. To enable the service to start on boot, run `sudo systemctl enable <servicename>`. Replace `<servicename>` with the name of your `.service` file (without the extension).

Use the following skeleton for your `systemd` file. Replace `{username}` with your username and `{deploy_secret}` with your random deploy secret.

```
[Unit]
Description=61A's internal Docker API
After=network.target

[Service]
User={username}
Group=www-data
WorkingDirectory=$hosted
Environment="DEPLOY_KEY={deploy_secret}"
ExecStartPre=/bin/bash -c 'source $hosted/env/bin/activate'
ExecStart=$hosted/env/bin/gunicorn --workers 3 --bind unix:api.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
```

## Using the API
For this section, we'll be using `example.com` as the deploy server.

### List running containers
`GET example.com`

This endpoint takes no parameters.

Sample Response
```json
{
    "app1": {
        "running": false,
        "image": "ubuntu:latest",
        "domains": ["app1.example.com", "app1-pr.example.com"]
    }
}
```

### Deploy a new container
`POST example.com/new`

Required Params
- `secret`: the deploy secret
- `image`: the name of the Docker Hub image, or the URL of the image

Optional Params
- `name`: a name to use, by default the name of the `image`
- `env`: a dictionary of environment variables to pass into the container

Sample Response
```
Running on app1.example.com!
```

### Stop a running container
`POST example.com/stop`

Required Params
- `secret`: the deploy secret
- `name`: the name of the container

Sample Response
```json
{
    "success": true
}
```

### Run a stopped container
`POST example.com/run`

Required Params
- `secret`: the deploy secret
- `name`: the name of the container

Sample Response
```json
{
    "success": false,
    "reason": "That container is already running."
}
```

### Add a domain to an existing container
`POST example.com/add_domain`

Required Params
- `secret`: the deploy secret
- `name`: the name of the container
- `domain`: the fully-qualified domain (minus the protocol) to add to the container

Sample Response
```json
{
    "success": true
}
```

### Delete a container
`POST example.com/delete`

Required Params
- `secret`: the deploy secret
- `name`: the name of the container

Sample Response
```json
{
    "success": false,
    "reason": "That container doesn't exist."
}
```

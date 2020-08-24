Office Hours Queue
==================

## Overview

Provides a web-based interface for requesting help during office hours.

Students request help on an assignment and question number from a location.

This app uses [Ok](https://okpy.org) to manage access. Even if you aren't using Ok for assignments, you should create a course on Ok and enroll all of your staff, academic interns, and students with the appropriate roles.

## For other courses

This is a hosted app provided by 61A. To set it up for your own course, visit [Auth](https://auth.apps.cs61a.org) and add the desired domain under `Domains`. Make sure that the OKPy endpoint and course name are what you expect. Then contact 61A staff for your queue to be activated. If you want to move the queue to a new OKPy course, update the endpoint on Auth - the change should be reflected in the queue within an hour.

## Installation

1. Clone this repo:

    ```
    git clone https://github.com/Cal-CS-61A-Staff/oh-queue.git
    ```
    Then cd into it:
    ```
    cd oh-queue
    ```

2. Create and activate a virtualenv:
    ```
    python3 -m virtualenv env  (If this does not work, try: `virtualenv -p python3 env`)
    source env/bin/activate
    ```

3. Use pip to install all the dependencies:
    ```
    pip install -r requirements.txt
    npm install
    ```

4. Run the database migrations to setup the initial database.
    ```
    ./manage.py resetdb
    ./manage.py seed_data
    ./manage.py db upgrade
    ```

5. Run the server:
    ```
    ./manage.py server
    ```

6. Point your browser to http://localhost:5000.  (This might take a while the first time.)

7. You can log in as any email while testing by going to http://localhost:5000/testing-login/.

### Dokku: Initial Deployment

    dokku apps:create app-name
    dokku clone app-name https://github.com/Cal-CS-61A-Staff/oh-queue
    dokku mysql:create db-name
    dokku mysql:link db-name app-name
    dokku domains:set app-name <domain>

    dokku config:set app-name OH_QUEUE_ENV=prod OK_KEY=<OK CLIENT> OK_SECRET=<OK SECRET> SECRET_KEY=<DB SECRET> AUTH_KEY=<AUTH_KEY> AUTH_SECRET=<AUTH_SECRET>
    dokku run app-name ./manage.py db upgrade
    dokku letsencrypt app-name
    # Change OK OAuth to support the domain

For `OK_KEY` and `OK_SECRET`, you'll need to create an Ok OAuth client [here](https://okpy.org/admin/clients) and have it approved by an Ok admin.

### Dokku: Upgrading

    dokku clone app-name https://github.com/Cal-CS-61A-Staff/oh-queue
    dokku run app-name ./manage.py db upgrade

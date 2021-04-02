
```{include} README.md
```

## CLI Utilities

This file contains miscellaneous utilities for command-line interfaces.

```{eval-rst}
.. automodule:: common.cli_utils
    :members:
```

## Course Configuration

This file contains various methods that can help identify a course as well as
determine the level of access a user (logged in with Okpy) has to the course.

```{eval-rst}
.. automodule:: common.course_config
    :members:
```

## Database Interface

This file contains the logic for interfacing with the 61A database backend,
or for interfacing with a local database if you don't have access to the
production database (or are developing something volatile).

By default, this code assumes that you are running locally without access to
the production database. As such, the default action is to create a local
`app.db` if an application requests to use a database. In production, the
environment variable `DATABASE_URL` is used to connect to the production
database.

To develop on the production database, use `ENV=DEV_ON_PROD` and pass in
`DATABASE_PW=password`, where `password` is the SQL password for the
`buildserver` user. Ask a Head of Software if you need access to this.

```{note}
Developing on production requires the Cloud SQL Proxy. Follow the instructions
at https://cloud.google.com/sql/docs/mysql/sql-proxy to install the proxy
in the root directory of the repository.
```

```{eval-rst}
.. automodule:: common.db
    :members:
```

## Hash Utilities

This file contains some utilities for hashing data.

```{eval-rst}
.. automodule:: common.hash_utils
    :members:
```

## HTML Helpers

This file contains some helpful HTML formatting tools for a standard frontend.

```{caution}
Do **not** use this library for student-facing apps, as it is vulnerable to XSS.
Only use it for quick staff-only frontends.
```

```{eval-rst}
.. automodule:: common.html
    :members:
```

## Job Routing

This file contains a decorator utility to add URL rules for recurring actions.

```{eval-rst}
.. automodule:: common.jobs
    :members:
```

## OAuth Client

This file contains some utilities for Okpy OAuth communication.

```{eval-rst}
.. automodule:: common.oauth_client
    :members:
```

## Secrets

This file contains some utilities to create/get secrets for an app.

```{eval-rst}
.. automodule:: common.secrets
    :members:
```

## Shell Utilities

This file contains some utilities to communicate with a shell.

```{eval-rst}
.. automodule:: common.shell_utils
    :members:
```

## `url_for`

This file creates a new `url_for` method to improve upon the default
{func}`~flask.url_for`.

```{eval-rst}
.. automodule:: common.url_for
    :members:
```

```{toctree}
:hidden:
:maxdepth: 3

rpc/README.md
```
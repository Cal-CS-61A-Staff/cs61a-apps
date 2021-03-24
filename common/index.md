
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
`buildserver` user.

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

```{eval-rst}
.. automodule:: common.hash_utils
    :members:
```

## HTML Helpers

```{eval-rst}
.. automodule:: common.html
    :members:
```

## Job Routing

```{eval-rst}
.. automodule:: common.jobs
    :members:
```

## OAuth Client

```{eval-rst}
.. automodule:: common.oauth_client
    :members:
```

## Secrets

```{eval-rst}
.. automodule:: common.secrets
    :members:
```

## Shell Utilities

```{eval-rst}
.. automodule:: common.shell_utils
    :members:
```

## `url_for`

```{eval-rst}
.. automodule:: common.url_for
    :members:
```

```{toctree}
:hidden:
:maxdepth: 3

rpc/README.md
```
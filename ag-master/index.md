```{include} README.md
```

## Data Models

There are 2 data models used by this app: `Assignment` and `Job`.

```{eval-rst}
.. automodule:: docs.ag_master.models
    :members:
```

## Utility Decorators

The autograder has two decorators that restrict access to various functions
and endpoints.

```{eval-rst}
.. automodule:: docs.ag_master.utils
    :members:
```

## Course Admin Endpoints

```{eval-rst}
.. automodule:: docs.ag_master.admin
    :members:
```

There is also a GUI available at autograder.cs61a.org for the following actions:
- Viewing all of a course's assignments (`/<course>`)
- Viewing a particular assignment (`/<course>/<assignment>`)
- Viewing a particular job (`/<course>/job/<id>`)
- Forcing unfinished jobs for an assignment to fail
  (`/<course>/<assignment>/fail_unfinished`)
- Retriggering failed jobs for an assignment
  (`/<course>/<assignment>/retrigger_unsuccessful`)

## Superadmin Endpoints

The following superadmin endpoint is available for viewing information about a
course: `/admin/<endpoint>`.

## Worker Communication

There are a few endpoints created solely to communicate grading jobs with the
worker instances.

```{eval-rst}
.. automodule:: docs.ag_master.worker
    :members:
```

## Okpy Communication

There are a few endpoints created to communicate job requests and outputs
between Okpy and the autograder. There is one RPC endpoint,
{func}`~common.rpc.ag_master.trigger_jobs`, and a handful of REST endpoints.
For the REST endpoints, see the next section.

```{eval-rst}
.. automodule:: docs.ag_master.okpy
    :members:
```

## API Model

This is the set of endpoints that will be used to communicate between Okpy
(or other grading base) and the autograder host. If you wish to recreate the
autograder, you will need to implement the following 3 endpoints. In addition,
you will likely need to get the contents of each backup that is being graded,
which can be done using the
[View a Backup](https://okpy.github.io/documentation/ok-api.html#backups-view-a-backup)
target of the Okpy API. You will also need to POST the scores output to Okpy,
which can be done using the
[Create a Score](https://okpy.github.io/documentation/ok-api.html#scores-create-a-score)
target of the Okpy API.

```{eval-rst}
.. openapi:: openapi.yml
```
# Generating Migrations

To generate migrations, you'll need to be running MySQL locally.

## Installing MySQL

### OSX

```
brew install mysql
```

Reccomended SQL Client for local exploration: [Sequel Pro](https://sequelpro.com/)

## Configuring MySQL
Start MySQL and connect
```
mysql.server start
mysql -u root
```
The password for root is blank by default. Just hit enter and you will enter the mysql console.
See the [MySQL docs](http://dev.mysql.com/doc/mysql-getting-started/en/) for more info.

Run the following commands to create a user and a table for OK

```
create database ohdevel;
CREATE USER 'ohdev'@'localhost';
GRANT ALL PRIVILEGES ON ohdevel.* TO 'ohdev'@'localhost';
```

## Running a migration

If the `master` branch is the current state of the production branch - start by checking out the master branch.

`git checkout master`

Make sure OK is using MySQL and not sqlite by setting the `DATABASE_URL`
environment variable. For Bash,
```
export DATABASE_URL=mysql://ohdev:@127.0.0.1:3306/ohdevel?charset=utf8mb4
```

```
# Rebuild the database
./manage.py resetdb
./manage.py db upgrade # Make sure this does not crash. If it does: see Common Errors below
```

Now you can checkout the branch with changes:

`git checkout feature-branch`

```
./manage.py db migrate -m "Added new feature"
```
That should produce the output along the lines of
```
INFO  [alembic.runtime.migration] Context impl MySQLImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.autogenerate.compare] Detected added column 'assignment.published_scores'
  Generating /dev/ok/server/migrations/versions/6ce2cf5c4534_publish_scores_for_assignments.py ... done
```

## Inspecting the output

Check the file contents before running the migrations to make sure the changes make sense. There should not be unncessary changes. It's ok to manually make changes to the script (or manually write a migration file) if needed.

## Deploying the migration.
Make sure the deploy the app. After it's running, run
```

dokku maintenance:on officehours-web # maintenance message
dokku mysql:stop officehours-web # stop mysql so the migration can get a lock
dokku mysql:start officehours-web # start it back up
# optionally stamp it with the previous revision (if it doesn't have a history of migrations)
# dokku run officehours-web ./manage.py db stamp 5e2ef12760a4
dokku run officehours-web ./manage.py db upgrade
dokku maintenance:off officehours-web
dokku deploy officehours-web  # to restart
```
to upgrade.

## Common errors

If you are getting long tracebacks that end in somethng like this
```
raise errorclass(errno, errorvalue)
sqlalchemy.exc.ProgrammingError: (pymysql.err.ProgrammingError) (1146, "Table 'ok-dev.client' doesn't exist") [SQL: 'ALTER TABLE client ADD COLUMN created DATETIME NOT NULL DEFAULT now()']
```
or
```
    raise util.CommandError("Target database is not up to date.")
alembic.util.exc.CommandError: Target database is not up to date.
```

It's likely that Alembic is trying to rerun migrations (or has not run all of the migrations in the folder)

If you are _sure_ that the DB is up to date - find the ID most recent migration run (the most recent commit in them migrations folder should reveal the file most recently created) and then run

```
./manage.py db stamp f7f27412d13f
```

This tells alembic that the DB is at revision `f7f27412d13f`. Now running `./manage.py db upgrade` should result in this output

```
$ ./manage.py db upgrade
INFO  [alembic.runtime.migration] Context impl MySQLImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
$
```

If that doesn't resolve it - make sure there are not unrun migrations in the branch.

If the upgrade is hanging - it might be unable to get a lock to the database.

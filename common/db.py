import os
import sys
from contextlib import contextmanager
from os import getenv
from os.path import exists
from time import sleep
from typing import List

import sqlalchemy.engine.url

from common.rpc.secrets import get_secret

use_devdb = getenv("ENV", "DEV") in ("DEV", "TEST")
use_prod_proxy = getenv("ENV") == "DEV_ON_PROD"

is_sphinx = "sphinx" in sys.argv[0]

if use_devdb:
    database_url = "sqlite:///" + os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "../app.db"
    )
elif use_prod_proxy:
    curr = os.path.abspath(os.path.curdir)
    prev = None
    while True:
        if ".git" in os.listdir(curr):
            app = os.path.basename(prev)
            break
        prev = curr
        curr = os.path.dirname(curr)
    assert (
        input(
            "Are you sure? You are about to use the PROD database on a DEV build (y/N) "
        )
        .strip()
        .lower()
        == "y"
    )
    if "cloud_sql_proxy" not in os.listdir(curr):
        print(
            "Follow the instructions at https://cloud.google.com/sql/docs/mysql/sql-proxy to install the proxy "
            "in the root directory of the repository, then try again."
        )
        exit(0)
    database_url = sqlalchemy.engine.url.URL(
        drivername="mysql+pymysql",
        username="buildserver",
        password=get_secret(secret_name="DATABASE_PW"),
        host="127.0.0.1",
        port=3307,
        database=app.replace("-", "_"),
    ).__to_string__(hide_password=False)
else:
    database_url = getenv("DATABASE_URL")

engine = sqlalchemy.create_engine(
    database_url,
    **(
        dict(
            connect_args=dict(
                ssl=dict(
                    cert="/shared/client-cert.pem",
                    key="/shared/client-key.pem",
                    ca="/shared/server-ca.pem",
                ),
            )
        )
        if exists("/shared/client-cert.pem")
        else {}
    ),
    **(
        {}
        if use_devdb
        else dict(pool_size=5, max_overflow=2, pool_timeout=30, pool_recycle=1800)
    ),
)


@contextmanager
def connect_db(*, retries=3):
    """Create a context that uses a connection to the current database.

    :param retries: the number of times to try connecting to the database
    :type retries: int

    :yields: a function with parameters ``(query: str, args: List[str] = [])``,
        where the ``query_str`` should use ``%s`` to represent sequential
        arguments in the ``args_list``

    :example usage:
    .. code-block:: python

        with connect_db() as db:
            db("INSERT INTO animals VALUES %s", ["cat"])
            output = db("SELECT * FROM animals")
    """
    if is_sphinx:

        def no_op(*args, **kwargs):
            class NoOp:
                fetchone = lambda *args: None
                fetchall = lambda *args: None

            return NoOp()

        yield no_op
    else:
        for i in range(retries):
            try:
                conn = engine.connect()
                break
            except:
                sleep(3)
                continue
        else:
            raise

        with conn:

            def db(query: str, args: List[str] = []):
                if use_devdb:
                    query = query.replace("%s", "?")
                return conn.execute(query, args)

            yield db


@contextmanager
def transaction_db():
    """Create a context that performs a transaction on current database.

    The difference between this and :meth:`~common.db.connect_db` is that this
    method batches queries in a transaction, and only runs them once the
    context is abandoned.

    :yields: a function with parameters ``(query: str, args: List[str] = [])``,
        where the ``query_str`` should use ``%s`` to represent sequential
        arguments in the ``args_list``

    :example usage:
    .. code-block:: python

        with transaction_db() as db:
            db("INSERT INTO animals VALUES %s", ["cat"])
            output = db("SELECT * FROM animals")
    """
    with engine.begin() as conn:

        def db(*args):
            query, *rest = args
            if use_devdb:
                query = query.replace("%s", "?")
            return conn.execute(query, *rest)

        yield db

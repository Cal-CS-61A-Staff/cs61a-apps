import os
from contextlib import contextmanager
from os import getenv

import sqlalchemy.engine.url


use_devdb = getenv("ENV", "DEV") in ("DEV", "TEST")

if use_devdb:
    database_url = "sqlite:///" + os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "../app.db"
    )
else:
    database_url = getenv("DATABASE_URL")

engine = sqlalchemy.create_engine(
    database_url,
    **(
        {}
        if use_devdb
        else dict(pool_size=5, max_overflow=2, pool_timeout=30, pool_recycle=1800)
    )
)


@contextmanager
def connect_db():
    with engine.connect() as conn:

        def db(*args):
            query, *rest = args
            if use_devdb:
                query = query.replace("%s", "?")
            return conn.execute(query, *rest)

        yield db

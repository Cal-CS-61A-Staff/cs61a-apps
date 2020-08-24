"""Added description requirement config

Revision ID: e4b5bd2a05cc
Revises: 56a1480bb7cc
Create Date: 2020-02-04 03:04:27.899172

"""

# revision identifiers, used by Alembic.
revision = 'e4b5bd2a05cc'
down_revision = '56a1480bb7cc'

from alembic import op
from sqlalchemy import orm
from oh_queue.models import *


def upgrade():
    connection = op.get_bind()
    session = orm.Session(bind=connection)

    session.commit()


def downgrade():
    # Get alembic DB bind
    connection = op.get_bind()
    session = orm.Session(bind=connection)

    session.commit()

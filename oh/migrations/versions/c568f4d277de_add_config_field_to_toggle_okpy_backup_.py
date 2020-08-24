"""add config field to toggle OKPy backup visibility

Revision ID: c568f4d277de
Revises: 3b7d60ea61e3
Create Date: 2020-04-06 14:22:14.162321

"""

# revision identifiers, used by Alembic.
from sqlalchemy import orm

revision = 'c568f4d277de'
down_revision = '3b7d60ea61e3'

from alembic import op
import sqlalchemy as sa
import oh_queue.models
from oh_queue.models import *


def upgrade():
    # Get alembic DB bind
    connection = op.get_bind()
    session = orm.Session(bind=connection)

    for course in session.query(ConfigEntry.course).distinct():
        session.add(ConfigEntry(key='show_okpy_backups', value='false', public=True, course=course[0]))

    session.commit()


def downgrade():
    pass

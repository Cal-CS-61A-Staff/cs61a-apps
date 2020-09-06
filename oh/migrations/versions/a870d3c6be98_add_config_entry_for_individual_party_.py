"""Add config entry for individual party tickets

Revision ID: a870d3c6be98
Revises: e96dc20c344a
Create Date: 2020-08-28 05:14:38.022254

"""
from sqlalchemy import orm

# revision identifiers, used by Alembic.
revision = 'a870d3c6be98'
down_revision = 'e96dc20c344a'

from alembic import op
import sqlalchemy as sa
import oh_queue.models
from oh_queue.models import *


def upgrade():
    # Get alembic DB bind
    connection = op.get_bind()
    session = orm.Session(bind=connection)

    for course in session.query(ConfigEntry.course).distinct():
        session.add(ConfigEntry(key='allow_private_party_tickets', value='true', public=True, course=course[0]))

    session.commit()


def downgrade():
    pass

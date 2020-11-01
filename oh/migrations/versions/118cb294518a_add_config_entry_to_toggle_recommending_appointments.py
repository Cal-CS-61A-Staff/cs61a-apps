"""add config entry to toggle recommending appointments

Revision ID: 118cb294518a
Revises: 00aea7233ef8
Create Date: 2020-09-09 00:44:39.274276

"""

# revision identifiers, used by Alembic.
revision = "118cb294518a"
down_revision = "ab9f3b203744"

from sqlalchemy import orm
from alembic import op
import sqlalchemy as sa
import oh_queue.models
from oh_queue.models import *


def upgrade():
    # Get alembic DB bind
    connection = op.get_bind()
    session = orm.Session(bind=connection)

    for course in session.query(ConfigEntry.course).distinct():
        session.add(
            ConfigEntry(
                key="recommend_appointments",
                value="true",
                public=True,
                course=course[0],
            )
        )

    session.commit()


def downgrade():
    pass

"""support ticket sort_key

Revision ID: 680b44ae9515
Revises: c2365b4ad424
Create Date: 2021-02-11 11:14:35.398091

"""

# revision identifiers, used by Alembic.
revision = "680b44ae9515"
down_revision = "c2365b4ad424"

from alembic import op
import sqlalchemy as sa
import oh_queue.models
from oh_queue.models import *

from datetime import datetime


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "ticket",
        sa.Column(
            "sort_key",
            sa.DateTime(),
            nullable=True,
        ),
    )
    op.execute("UPDATE ticket SET sort_key=created")
    op.alter_column("ticket", "sort_key", nullable=False)
    op.create_index(op.f("ix_ticket_sort_key"), "ticket", ["sort_key"], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_ticket_sort_key"), table_name="ticket")
    op.drop_column("ticket", "sort_key")
    # ### end Alembic commands ###

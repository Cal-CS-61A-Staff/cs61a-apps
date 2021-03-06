"""removed uniqueness constraints

Revision ID: 7857a34ef101
Revises: None
Create Date: 2020-03-08 05:38:00.904655

"""

# revision identifiers, used by Alembic.
revision = "7857a34ef101"
down_revision = None

from alembic import op
import sqlalchemy as sa
import oh_queue.models
from oh_queue.models import *


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index("name", table_name="assignment")
    op.drop_index("name", table_name="location")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_index("name", "location", ["name"], unique=True)
    op.create_index("name", "assignment", ["name"], unique=True)
    # ### end Alembic commands ###

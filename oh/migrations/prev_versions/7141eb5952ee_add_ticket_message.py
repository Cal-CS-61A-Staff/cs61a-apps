"""add ticket message

Revision ID: 7141eb5952ee
Revises: e330a9be55f8
Create Date: 2020-03-02 18:02:22.699824

"""

# revision identifiers, used by Alembic.
revision = '7141eb5952ee'
down_revision = 'e330a9be55f8'

from alembic import op
import sqlalchemy as sa
import oh_queue.models
from sqlalchemy import orm
from oh_queue.models import *


def upgrade():
    pass

def downgrade():
    pass

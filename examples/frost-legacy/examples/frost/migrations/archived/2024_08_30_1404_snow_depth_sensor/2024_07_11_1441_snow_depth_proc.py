"""snow_depth_proc

Revision ID: 9ee1798eb5ff
Revises: 0510608df920
Create Date: 2024-07-11 14:41:43.620943

"""

import sqlalchemy as sa
from alembic import op

from schemas.other_objects.functions import usp_InsertSnowDepthReading

# revision identifiers, used by Alembic.
revision = "9ee1798eb5ff"
down_revision = "0510608df920"
branch_labels = None
depends_on = None


def upgrade() -> None:
    usp_InsertSnowDepthReading.create_function(op)


def downgrade() -> None:
    usp_InsertSnowDepthReading.drop_function(op)

"""images-projection_table_drop_table

Revision ID: c4296fe9604b
Revises: 044a15a21953
Create Date: 2025-07-09 14:16:38.998837

"""

import sqlalchemy as sa
from alembic import op

from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "c4296fe9604b"
down_revision = "044a15a21953"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(read_sql_file("DropTempTable", clickhouse=True))


def downgrade() -> None:
    pass

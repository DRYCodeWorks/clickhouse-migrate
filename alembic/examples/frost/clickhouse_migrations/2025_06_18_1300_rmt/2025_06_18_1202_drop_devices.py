"""drop-devices

Revision ID: 8d761ccc553d
Revises: 40b27bf3e405
Create Date: 2025-06-18 12:02:28.389176

"""

import sqlalchemy as sa
from alembic import op

from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "8d761ccc553d"
down_revision = "40b27bf3e405"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS devices")


def downgrade() -> None:
    op.execute(read_sql_file("CreateDevices", clickhouse=True))

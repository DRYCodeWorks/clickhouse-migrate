"""create-devices-table

Revision ID: aa91e88bfc0f
Revises: 0b8351f26d9a
Create Date: 2025-04-08 13:25:10.265740

"""

import sqlalchemy as sa
from alembic import op

from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "aa91e88bfc0f"
down_revision = "0b8351f26d9a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    data = read_sql_file("CreateDevices", clickhouse=True)
    op.execute(data)


def downgrade() -> None:
    op.drop_table("devices")

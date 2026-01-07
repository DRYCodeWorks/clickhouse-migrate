"""rmt-sds

Revision ID: 00dbe665d96f
Revises: 8d761ccc553d
Create Date: 2025-06-18 12:18:44.524174

"""

import sqlalchemy as sa
from alembic import op

from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "00dbe665d96f"
down_revision = "8d761ccc553d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(read_sql_file("CreateSDSReadingsRMT", clickhouse=True))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS sds_readings")
    op.execute(read_sql_file("CreateSDSReadings", clickhouse=True))

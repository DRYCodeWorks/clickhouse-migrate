"""create-sds-readings-table

Revision ID: 15b4fa6f41fe
Revises: 62dba0fe8020
Create Date: 2025-04-08 14:11:42.679853

"""

import sqlalchemy as sa
from alembic import op

from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "15b4fa6f41fe"
down_revision = "62dba0fe8020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    data = read_sql_file("CreateSDSReadings", clickhouse=True)
    op.execute(data)


def downgrade() -> None:
    op.drop_table("sds_readings")

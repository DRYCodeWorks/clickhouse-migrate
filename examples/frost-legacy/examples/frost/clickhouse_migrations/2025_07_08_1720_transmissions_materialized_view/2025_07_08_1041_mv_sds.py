"""mv-sds

Revision ID: 3f75c81e0daf
Revises: 56c950cf9658
Create Date: 2025-07-08 10:41:42.392914

"""

import sqlalchemy as sa
from alembic import op

from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "3f75c81e0daf"
down_revision = "56c950cf9658"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(read_sql_file("CreateSDSMVTable", clickhouse=True))
    op.execute(read_sql_file("CreateSDSMaterializedView", clickhouse=True))
    op.execute(read_sql_file("SDSLoadMaterializedView", clickhouse=True))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS get_latest_sds_readings;")
    op.execute("DROP TABLE IF EXISTS latest_sds_readings;")

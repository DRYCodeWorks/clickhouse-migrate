"""transmissions-rmt-partition

Revision ID: 40b27bf3e405
Revises: f42635c64e95
Create Date: 2025-06-18 10:21:33.755605

"""

import sqlalchemy as sa
from alembic import op

from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "40b27bf3e405"
down_revision = "f42635c64e95"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(read_sql_file("CreateTransmissionsRMT", clickhouse=True))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS transmissions")
    op.execute(read_sql_file("CreateTransmissions", clickhouse=True))

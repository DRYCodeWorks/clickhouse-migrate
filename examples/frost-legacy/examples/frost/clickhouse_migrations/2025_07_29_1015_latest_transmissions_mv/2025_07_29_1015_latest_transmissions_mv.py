"""latest_transmissions_mv

Revision ID: dd5f4052f531
Revises: c4296fe9604b
Create Date: 2025-07-29 10:15:16.208548

"""

from alembic import op
from helpers.utils import read_sql_file
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "dd5f4052f531"
down_revision = "c4296fe9604b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(read_sql_file("CreateLatestTransmissionsMVTable", clickhouse=True))
    op.execute(
        read_sql_file("CreateLatestTransmissionsMaterializedView", clickhouse=True)
    )
    op.execute(read_sql_file("LatestTransmissionsLoad", clickhouse=True))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS latest_transmissions;")
    op.execute("DROP TABLE IF EXISTS get_latest_transmissions;")

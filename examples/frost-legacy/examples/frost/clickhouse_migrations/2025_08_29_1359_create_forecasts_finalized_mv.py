"""create_mv_forecasts_deduplicator

Revision ID: 9f5d2c3e7a4b
Revises: 7c3e4f9a8b12
Create Date: 2025-08-29 13:59:00.000000

"""

from alembic import op
import sqlalchemy as sa
from helpers.utils import read_sql_file


# revision identifiers, used by Alembic.
revision = "9f5d2c3e7a4b"
down_revision = "7c3e4f9a8b12"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(read_sql_file("Create_MV_ForecastsDeduplicator", clickhouse=True))


def downgrade() -> None:
    op.execute("DROP VIEW _mv_forecasts_deduplicator")
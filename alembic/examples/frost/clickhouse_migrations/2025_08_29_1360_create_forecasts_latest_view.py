"""create_view_forecasts_latest

Revision ID: a2b5c8d9f3e7
Revises: 9f5d2c3e7a4b
Create Date: 2025-08-29 13:60:00.000000

"""

from alembic import op
import sqlalchemy as sa
from helpers.utils import read_sql_file


# revision identifiers, used by Alembic.
revision = "a2b5c8d9f3e7"
down_revision = "9f5d2c3e7a4b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(read_sql_file("CreateViewForecastsLatest", clickhouse=True))


def downgrade() -> None:
    op.execute("DROP VIEW v_forecasts_latest")
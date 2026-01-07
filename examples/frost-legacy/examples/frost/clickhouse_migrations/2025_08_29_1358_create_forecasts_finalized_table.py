"""createbest_known_forecasts_table

Revision ID: 7c3e4f9a8b12
Revises: 1b7c9aeb0bf9
Create Date: 2025-08-29 13:58:00.000000

"""

from alembic import op
import sqlalchemy as sa
from helpers.utils import read_sql_file


# revision identifiers, used by Alembic.
revision = "7c3e4f9a8b12"
down_revision = "1b7c9aeb0bf9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(read_sql_file("Create_ForecastsDeduplicatedTable", clickhouse=True))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS best_known_forecasts")
"""create_transmissions_with_forecasts_table

Revision ID: b4d87adf4aea
Revises: a2b5c8d9f3e7
Create Date: 2025-08-29 14:00:39.507789

"""

from alembic import op
import sqlalchemy as sa
from helpers.utils import read_sql_file


# revision identifiers, used by Alembic.
revision = "b4d87adf4aea"
down_revision = "a2b5c8d9f3e7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(read_sql_file("CreateTransmissionsWithForecastsTable", clickhouse=True))


def downgrade() -> None:
    op.execute("DROP TABLE transmissions_with_forecasts")

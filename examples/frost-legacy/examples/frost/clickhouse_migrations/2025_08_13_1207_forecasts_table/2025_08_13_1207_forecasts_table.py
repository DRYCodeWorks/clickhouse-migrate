"""forecasts_table

Revision ID: f436c220f48c
Revises: dd5f4052f531
Create Date: 2025-08-13 12:07:36.744272

"""

import sqlalchemy as sa
from alembic import op

from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "f436c220f48c"
down_revision = "dd5f4052f531"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(read_sql_file("AddForecastsTable", clickhouse=True))


def downgrade() -> None:
    op.execute("DROP TABLE forecasts")

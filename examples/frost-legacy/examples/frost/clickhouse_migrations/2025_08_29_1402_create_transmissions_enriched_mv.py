"""create_mv_transmissions_forecast_joiner

Revision ID: c2ac8ab7728f
Revises: b4d87adf4aea
Create Date: 2025-08-29 14:02:26.340724

"""

import sqlalchemy as sa
from alembic import op

from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "c2ac8ab7728f"
down_revision = "b4d87adf4aea"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        read_sql_file("Create_MV_TransmissionsForecastJoiner", clickhouse=True)
    )


def downgrade() -> None:
    op.execute("DROP VIEW _mv_transmissions_forecast_joiner")

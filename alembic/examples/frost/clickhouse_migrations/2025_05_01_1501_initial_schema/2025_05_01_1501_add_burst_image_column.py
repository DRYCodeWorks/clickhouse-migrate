"""add-burst-image-column

Revision ID: c8d4b455ed26
Revises: 15b4fa6f41fe
Create Date: 2025-05-01 15:01:03.170040

"""

import sqlalchemy as sa
from alembic import op

from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "c8d4b455ed26"
down_revision = "15b4fa6f41fe"
branch_labels = None
depends_on = None


def upgrade() -> None:
    data = read_sql_file("AddBurstImage", clickhouse=True)
    op.execute(data)


def downgrade() -> None:
    op.execute("ALTER TABLE images DROP COLUMN IsBurstImage")

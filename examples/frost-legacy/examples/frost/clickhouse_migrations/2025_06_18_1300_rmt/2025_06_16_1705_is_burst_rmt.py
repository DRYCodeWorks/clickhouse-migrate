"""is-burst-rmt

Revision ID: f42635c64e95
Revises: 7589cf670bae
Create Date: 2025-06-16 17:05:47.783609

"""

import sqlalchemy as sa
from alembic import op

from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "f42635c64e95"
down_revision = "7589cf670bae"
branch_labels = None
depends_on = None


def upgrade() -> None:
    data = read_sql_file("AddBurstImage", clickhouse=True)
    op.execute(data)


def downgrade() -> None:
    op.execute("ALTER TABLE images DROP COLUMN IsBurstImage")

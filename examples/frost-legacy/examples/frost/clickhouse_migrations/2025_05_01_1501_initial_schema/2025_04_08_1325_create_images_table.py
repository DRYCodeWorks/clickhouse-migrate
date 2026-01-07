"""create-images-table

Revision ID: 09fae6c3f0dc
Revises: aa91e88bfc0f
Create Date: 2025-04-08 13:25:18.572037

"""

import sqlalchemy as sa
from alembic import op

from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "09fae6c3f0dc"
down_revision = "aa91e88bfc0f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    data = read_sql_file("CreateImages", clickhouse=True)
    op.execute(data)


def downgrade() -> None:
    op.drop_table("images")

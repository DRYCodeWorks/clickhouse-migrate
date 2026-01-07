"""create-transmissions-table

Revision ID: 62dba0fe8020
Revises: 09fae6c3f0dc
Create Date: 2025-04-08 13:25:24.472875

"""

import sqlalchemy as sa
from alembic import op

from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "62dba0fe8020"
down_revision = "09fae6c3f0dc"
branch_labels = None
depends_on = None


def upgrade() -> None:
    data = read_sql_file("CreateTransmissions", clickhouse=True)
    op.execute(data)


def downgrade() -> None:
    op.drop_table("transmissions")

"""sds-readings

Revision ID: 2db4682a61b6
Revises: fa48d536e9e4
Create Date: 2025-06-18 13:00:41.179878

"""

import sqlalchemy as sa
from alembic import op

from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "2db4682a61b6"
down_revision = "fa48d536e9e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(read_sql_file("CreateSDSReadings", clickhouse=True))


def downgrade() -> None:
    pass

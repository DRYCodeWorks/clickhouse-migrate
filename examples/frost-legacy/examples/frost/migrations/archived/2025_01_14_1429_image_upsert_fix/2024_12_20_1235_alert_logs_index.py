"""alert-logs-index

Revision ID: 32265edd8275
Revises: 360085af62c5
Create Date: 2024-12-20 12:35:46.173306

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "32265edd8275"
down_revision = "360085af62c5"
branch_labels = None
depends_on = None


INDEX_NAME = "iDX_AlertLogsNew_DeviceID_Includes_AlertID_SentDateTimeUTC"
TABLE_NAME = "AlertLogsNew"


def upgrade() -> None:
    op.create_index(
        INDEX_NAME,
        TABLE_NAME,
        ["DeviceID"],
        unique=False,
        mssql_include=["AlertID", "SentDateTimeUTC"],
    )


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name=TABLE_NAME)

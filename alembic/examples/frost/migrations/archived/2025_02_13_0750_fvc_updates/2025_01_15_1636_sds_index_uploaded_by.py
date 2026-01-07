"""sds-index-uploaded-by

Revision ID: 6ff6ac15dc1a
Revises: 0ce987bc5cb7
Create Date: 2025-01-15 16:36:49.430837

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "6ff6ac15dc1a"
down_revision = "0ce987bc5cb7"
branch_labels = None
depends_on = None

INDEX_NAME = "ix_UploadedBy_Includes_CaptureDateTimeUTC"
TABLE_NAME = "SnowDepthReadings"


def upgrade() -> None:
    op.create_index(
        INDEX_NAME,
        TABLE_NAME,
        ["UploadedByRWIS", sa.text("[CaptureDateTimeUTC] DESC")],
        unique=False,
        mssql_include=["DeviceID"],
    )


def downgrade() -> None:
    op.drop_index(INDEX_NAME, table_name=TABLE_NAME)

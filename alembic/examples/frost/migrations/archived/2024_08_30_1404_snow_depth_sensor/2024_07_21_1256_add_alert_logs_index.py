"""add_alert_logs_index

Revision ID: 0c651d3c3936
Revises: e1545a7a0c7b
Create Date: 2024-07-25 12:56:23.622593

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0c651d3c3936"
down_revision = "e1545a7a0c7b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_AlertID_DeviceID_Includes",
        "AlertLogs",
        ["AlertID", "DeviceID"],
        unique=False,
        mssql_include=[
            "LatestTransmissionDateTimeUTC",
            "NextForecastDateTimeUTC",
            "SentDateTimeUTC",
        ],
    )
    op.create_index(
        "ix_IsCompleteCaptureDateTimeUTC_Includes",
        "DeviceImages",
        ["IsComplete", "CaptureDateTimeUTC"],
        unique=False,
        mssql_include=["ID"],
    )


def downgrade() -> None:
    op.drop_index("ix_AlertID_DeviceID_Includes", table_name="AlertLogs")
    op.drop_index("ix_IsCompleteCaptureDateTimeUTC_Includes", table_name="DeviceImages")

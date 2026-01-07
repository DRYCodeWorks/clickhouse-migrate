"""add threshold snapshots to storm events

Revision ID: fdc989d0c108
Revises: ae47b98b86b7
Create Date: 2025-08-14 16:00:00.000000

"""

import logging

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql

# revision identifiers, used by Alembic.
revision = "fdc989d0c108"
down_revision = "ae47b98b86b7"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)


def upgrade():
    """Add StartThresholdSnapshot and EndThresholdSnapshot columns to StormEvents table"""

    # Add StartThresholdSnapshot column to capture thresholds used for storm start detection
    op.add_column(
        "StormEvents",
        sa.Column("StartThresholdSnapshot", mssql.JSON(True), nullable=True),
    )

    # Add EndThresholdSnapshot column to capture thresholds used for storm end detection
    op.add_column(
        "StormEvents",
        sa.Column("EndThresholdSnapshot", mssql.JSON(True), nullable=True),
    )

    logger.info(
        "Added StartThresholdSnapshot and EndThresholdSnapshot columns to StormEvents table"
    )


def downgrade():
    """Remove threshold snapshot columns from StormEvents table"""

    # Drop EndThresholdSnapshot column
    op.drop_column("StormEvents", "EndThresholdSnapshot")

    # Drop StartThresholdSnapshot column
    op.drop_column("StormEvents", "StartThresholdSnapshot")

    logger.info("Removed threshold snapshot columns from StormEvents table")

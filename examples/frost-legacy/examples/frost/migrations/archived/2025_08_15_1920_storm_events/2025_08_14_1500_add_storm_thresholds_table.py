"""add storm thresholds table

Revision ID: ae47b98b86b7
Revises: 4d5e6f7a8b9c
Create Date: 2025-08-14 15:00:00.000000

"""

import logging

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = "ae47b98b86b7"
down_revision = "4d5e6f7a8b9c"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)


def upgrade():
    """Create StormThresholds table for device-level threshold configuration"""

    # Create StormThresholds table with device-level design
    op.create_table(
        "StormThresholds",
        sa.Column(
            "ID", sa.Integer(), sa.Identity(start=1, increment=1), nullable=False
        ),
        sa.Column("DeviceID", sa.BigInteger(), nullable=True),  # NULL = Frost defaults
        sa.Column("StormTypeID", sa.SmallInteger(), nullable=False),
        sa.Column("StartRules", mssql.JSON(True), nullable=True),
        sa.Column("EndRules", mssql.JSON(True), nullable=True),
        sa.Column(
            "IsActive", sa.Boolean(), nullable=False, server_default=text("((1))")
        ),
        sa.Column(
            "CreatedDateTimeUTC",
            mssql.DATETIME2(3),
            nullable=False,
            server_default=text("(getutcdate())"),
        ),
        sa.Column("CreatedUserID", mssql.UNIQUEIDENTIFIER(), nullable=True),
        sa.Column("ModifiedDateTimeUTC", mssql.DATETIME2(3), nullable=True),
        sa.Column("ModifiedUserID", mssql.UNIQUEIDENTIFIER(), nullable=True),
        sa.PrimaryKeyConstraint("ID"),
        sa.ForeignKeyConstraint(["DeviceID"], ["Devices.ID"]),
        sa.ForeignKeyConstraint(["StormTypeID"], ["StormType.ID"]),
        sa.ForeignKeyConstraint(["CreatedUserID"], ["Users.ID"]),
        sa.ForeignKeyConstraint(["ModifiedUserID"], ["Users.ID"]),
        sa.UniqueConstraint(
            "DeviceID", "StormTypeID", name="UQ_StormThresholds_DeviceID_StormTypeID"
        ),
    )

    # Create index for efficient lookups
    op.create_index(
        "IDX_StormThresholds_DeviceID_StormTypeID",
        "StormThresholds",
        ["DeviceID", "StormTypeID"],
    )

    # Note: Default threshold values will be added later once the rules engine is implemented
    # For now, the table structure is in place to support device-specific thresholds

    logger.info("Created StormThresholds table with device-level design")


def downgrade():
    """Remove StormThresholds table"""

    # Drop index
    op.drop_index(
        "IDX_StormThresholds_DeviceID_StormTypeID", table_name="StormThresholds"
    )

    # Drop table
    op.drop_table("StormThresholds")

    logger.info("Dropped StormThresholds table")

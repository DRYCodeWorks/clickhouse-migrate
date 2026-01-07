"""add threshold procedures and functions

Revision ID: dcac1ec2177d
Revises: fdc989d0c108
Create Date: 2025-08-14 17:00:00.000000

"""

import logging

from alembic import op

# Import our versioned procedure and function classes
from schemas.functions import fn_GetStormThresholds_v1
from schemas.stored_procedures import (
    sp_CompleteStormEvent_v1,
    sp_CreateStormEvent_v2,
    sp_UpsertDeviceThreshold_v1,
)

# revision identifiers, used by Alembic.
revision = "dcac1ec2177d"
down_revision = "fdc989d0c108"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)


def upgrade() -> None:
    """Deploy storm threshold-related functions and stored procedures"""

    # Create the threshold function first (needed by stored procedures)
    fn_GetStormThresholds_v1.create_function(op)
    logger.info("Created fn_GetStormThresholds_v1")

    # Create threshold management procedures
    sp_UpsertDeviceThreshold_v1.create_function(op)
    logger.info("Created sp_UpsertDeviceThreshold_v1")

    # Create v2 storm event procedures with threshold support
    sp_CreateStormEvent_v2.create_function(op)
    logger.info("Created sp_CreateStormEvent_v2")

    sp_CompleteStormEvent_v1.create_function(op)
    logger.info("Created sp_CompleteStormEvent_v1")


def downgrade() -> None:
    """Remove storm threshold-related functions and stored procedures"""

    # Drop procedures in reverse order
    sp_CompleteStormEvent_v1.drop_function(op)
    logger.info("Dropped sp_CompleteStormEvent_v1")

    sp_CreateStormEvent_v2.drop_function(op)
    logger.info("Dropped sp_CreateStormEvent_v2")

    sp_UpsertDeviceThreshold_v1.drop_function(op)
    logger.info("Dropped sp_UpsertDeviceThreshold_v1")

    # Drop function last
    fn_GetStormThresholds_v1.drop_function(op)
    logger.info("Dropped fn_GetStormThresholds_v1")
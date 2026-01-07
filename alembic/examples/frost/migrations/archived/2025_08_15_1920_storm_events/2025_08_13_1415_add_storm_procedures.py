"""add_storm_procedures

Revision ID: 4d5e6f7a8b9c
Revises: 5ad77b1feebb
Create Date: 2025-08-13 14:15:00.000000

"""

import sqlalchemy as sa
from alembic import op

# Import our versioned procedure classes
from schemas.stored_procedures import (
    sp_CreateRetroactiveStormEvents_v1,
    sp_CreateStormEvent_v1,
    sp_UpdateStormStatus_v1,
)

# revision identifiers, used by Alembic.
revision = "4d5e6f7a8b9c"
down_revision = "5ad77b1feebb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Deploy storm-related stored procedures with version suffixes"""

    # Create the storm event management procedures
    # These will create: sp_CreateStormEvent_v1, sp_UpdateStormStatus_v1, sp_CreateRetroactiveStormEvents_v1
    # With permissions for: device_portal_api
    sp_CreateStormEvent_v1.create_function(op)
    sp_UpdateStormStatus_v1.create_function(op)
    sp_CreateRetroactiveStormEvents_v1.create_function(op)


def downgrade() -> None:
    """Remove storm-related stored procedures"""

    # Drop procedures in reverse order
    sp_CreateRetroactiveStormEvents_v1.drop_function(op)
    sp_UpdateStormStatus_v1.drop_function(op)
    sp_CreateStormEvent_v1.drop_function(op)

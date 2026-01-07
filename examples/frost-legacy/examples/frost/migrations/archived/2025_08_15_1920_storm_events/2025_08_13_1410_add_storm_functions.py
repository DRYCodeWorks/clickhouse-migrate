"""add_storm_functions

Revision ID: 5ad77b1feebb
Revises: 42c8f57b7768
Create Date: 2025-08-13 14:10:00.000000

"""

import sqlalchemy as sa
from alembic import op

# Import our versioned function class
from schemas.functions import fn_GenerateStormName_v1

# revision identifiers, used by Alembic.
revision = "5ad77b1feebb"
down_revision = "42c8f57b7768"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Deploy storm-related functions with version suffixes"""

    # Create the storm name generation function
    # This will create: fn_GenerateStormName_v1
    # With permissions for: device_portal_api
    fn_GenerateStormName_v1.create_function(op)


def downgrade() -> None:
    """Remove storm-related functions"""

    # Drop function
    fn_GenerateStormName_v1.drop_function(op)

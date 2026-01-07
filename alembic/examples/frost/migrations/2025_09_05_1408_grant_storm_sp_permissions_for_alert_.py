"""grant_storm_sp_permissions_for_alert_engine

Revision ID: 54281435490a
Revises: 7c77c4f44629
Create Date: 2025-09-05 14:08:54.650514

"""

from alembic import op
import sqlalchemy as sa
from schemas.stored_procedures import (
    sp_UpdateStormStatus_v1,
    sp_CreateStormEvent_v2,
    sp_CompleteStormEvent_v1,
)

# revision identifiers, used by Alembic.
revision = "54281435490a"
down_revision = "7c77c4f44629"
branch_labels = None
depends_on = None


def upgrade() -> None:
    sp_UpdateStormStatus_v1.drop_function(op)
    sp_UpdateStormStatus_v1.create_function(op)

    sp_CreateStormEvent_v2.drop_function(op)
    sp_CreateStormEvent_v2.create_function(op)

    sp_CompleteStormEvent_v1.drop_function(op)
    sp_CompleteStormEvent_v1.create_function(op)


def downgrade() -> None:
    sp_UpdateStormStatus_v1.create_function(op)
    sp_CreateStormEvent_v2.create_function(op)
    sp_CompleteStormEvent_v1.create_function(op)

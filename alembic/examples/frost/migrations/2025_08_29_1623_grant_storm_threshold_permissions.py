"""grant_storm_threshold_permissions

Revision ID: 0811cc2b9d7b
Revises: 32f486755bfb
Create Date: 2025-08-29 16:23:38.251823

"""

from alembic import op
import sqlalchemy as sa
from schemas.functions import fn_GetStormThresholds_v1

# revision identifiers, used by Alembic.
revision = "0811cc2b9d7b"
down_revision = "32f486755bfb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    fn_GetStormThresholds_v1.drop_function(op)
    fn_GetStormThresholds_v1.create_function(op)


def downgrade() -> None:
    fn_GetStormThresholds_v1.create_function(op)

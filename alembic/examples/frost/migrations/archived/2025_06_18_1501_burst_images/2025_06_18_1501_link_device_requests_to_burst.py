"""link-device-requests-to-burst

Revision ID: b3c039a75436
Revises: 04606e6e4ca7
Create Date: 2025-06-18 15:01:32.659290

"""

import sqlalchemy as sa
from alembic import op

from schemas.functions import fn_GetDeviceRequestID, fn_GetDeviceRequestID_DEPRECATED

# revision identifiers, used by Alembic.
revision = "b3c039a75436"
down_revision = "04606e6e4ca7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    fn_GetDeviceRequestID_DEPRECATED.drop_function(op)
    fn_GetDeviceRequestID.create_function(op)


def downgrade() -> None:
    fn_GetDeviceRequestID.drop_function(op)
    fn_GetDeviceRequestID_DEPRECATED.create_function(op)

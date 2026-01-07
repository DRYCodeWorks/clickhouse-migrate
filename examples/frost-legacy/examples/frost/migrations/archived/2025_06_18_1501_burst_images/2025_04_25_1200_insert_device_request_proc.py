"""insert-device-request-proc

Revision ID: 04606e6e4ca7
Revises: 32879064aa8f
Create Date: 2025-04-25 12:00:47.522110

"""

import sqlalchemy as sa
from alembic import op

from schemas.stored_procedures import (
    usp_api_InsertDeviceRequest,
    usp_api_InsertDeviceRequest_rollback,
)

# revision identifiers, used by Alembic.
revision = "04606e6e4ca7"
down_revision = "32879064aa8f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    usp_api_InsertDeviceRequest_rollback.drop_function(op)
    usp_api_InsertDeviceRequest.create_function(op)


def downgrade() -> None:
    usp_api_InsertDeviceRequest.drop_function(op)
    usp_api_InsertDeviceRequest_rollback.create_function(op)

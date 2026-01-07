"""isburstimage-proc

Revision ID: 8b8b024f50c9
Revises: b862baddcdcd
Create Date: 2025-04-17 16:14:12.723660

"""

import sqlalchemy as sa
from alembic import op

from schemas.stored_procedures import (
    usp_api_UpsertCompletedImage,
    usp_api_UpsertCompletedImage_rollback,
    usp_utl_InsertDeviceImages,
    usp_utl_InsertDeviceImages_rollback,
)

# revision identifiers, used by Alembic.
revision = "8b8b024f50c9"
down_revision = "b862baddcdcd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    usp_utl_InsertDeviceImages_rollback.drop_function(op)
    usp_utl_InsertDeviceImages.create_function(op)
    usp_api_UpsertCompletedImage_rollback.drop_function(op)
    usp_api_UpsertCompletedImage.create_function(op)


def downgrade() -> None:
    usp_api_UpsertCompletedImage.drop_function(op)
    usp_api_UpsertCompletedImage_rollback.create_function(op)
    usp_utl_InsertDeviceImages.drop_function(op)
    usp_utl_InsertDeviceImages_rollback.create_function(op)

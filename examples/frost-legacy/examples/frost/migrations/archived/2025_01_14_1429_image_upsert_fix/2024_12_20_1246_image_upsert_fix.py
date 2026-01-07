"""image_upsert_fix

This revision attempts to fix a deadlocking issue with the image upserts.

Revision ID: ab3ae58d8250
Revises: 530a79ad905b
Create Date: 2024-12-11 10:16:03.601656

"""

import sqlalchemy as sa
from alembic import op

from schemas.other_objects.functions import (
    UpsertCompletedImageFeature,
    usp_utl_InsertDeviceImagesV2,
)

# revision identifiers, used by Alembic.
revision = "ab3ae58d8250"
down_revision = "530a79ad905b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    UpsertCompletedImageFeature["usp_utl_InsertDeviceImages"].drop_function(op)
    usp_utl_InsertDeviceImagesV2.create_function(op)


def downgrade() -> None:
    usp_utl_InsertDeviceImagesV2.drop_function(op)
    UpsertCompletedImageFeature["usp_utl_InsertDeviceImages"].create_function(op)

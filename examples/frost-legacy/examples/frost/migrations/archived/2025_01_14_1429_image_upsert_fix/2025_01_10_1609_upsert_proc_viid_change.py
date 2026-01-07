"""upsert-proc-viid-change

Revision ID: 0ce987bc5cb7
Revises: a9799105213f
Create Date: 2025-01-10 16:09:23.417495

"""

import sqlalchemy as sa
from alembic import op

from schemas.other_objects.functions import (
    UpsertCompletedImageFeature,
    usp_api_UpsertCompletedImage,
    usp_utl_InsertDeviceImagesV2,
    usp_utl_InsertDeviceImagesV3,
)

# revision identifiers, used by Alembic.
revision = "0ce987bc5cb7"
down_revision = "a9799105213f"
branch_labels = None
depends_on = None

prev_UpsertCompletedImageFeature = UpsertCompletedImageFeature[
    "usp_api_UpsertCompletedImage"
]


def upgrade() -> None:
    prev_UpsertCompletedImageFeature.drop_function(op)
    usp_utl_InsertDeviceImagesV2.drop_function(op)
    usp_api_UpsertCompletedImage.create_function(op)
    usp_utl_InsertDeviceImagesV3.create_function(op)


def downgrade() -> None:
    usp_api_UpsertCompletedImage.drop_function(op)
    usp_utl_InsertDeviceImagesV3.drop_function(op)
    prev_UpsertCompletedImageFeature.create_function(op)
    usp_utl_InsertDeviceImagesV2.create_function(op)

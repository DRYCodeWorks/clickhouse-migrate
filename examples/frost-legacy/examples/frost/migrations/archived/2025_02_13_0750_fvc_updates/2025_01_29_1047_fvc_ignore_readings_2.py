"""fvc-ignore-readings

Revision ID: cbfaa34afe0c
Revises: 6ff6ac15dc1a
Create Date: 2025-01-16 11:43:04.995971

"""

import sqlalchemy as sa
from alembic import op

from schemas.stored_procedures import (
    usp_api_UpsertCompletedImage,
    usp_api_UpsertCompletedImage_rollback,
)

# revision identifiers, used by Alembic.
revision = "cbfaa34afe0c"
down_revision = "ed909dfdb403"
branch_labels = None
depends_on = None


def upgrade() -> None:
    usp_api_UpsertCompletedImage_rollback.drop_function(op)
    usp_api_UpsertCompletedImage.create_function(op)


def downgrade() -> None:
    usp_api_UpsertCompletedImage.drop_function(op)
    usp_api_UpsertCompletedImage_rollback.create_function(op)

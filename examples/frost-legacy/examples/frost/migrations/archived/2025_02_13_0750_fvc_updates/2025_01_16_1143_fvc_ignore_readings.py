"""fvc-ignore-readings

Revision ID: ed909dfdb403
Revises: 6ff6ac15dc1a
Create Date: 2025-01-16 11:43:04.995971

"""

import sqlalchemy as sa
from alembic import op

from schemas.stored_procedures import (
    usp_api_UpsertDeviceReading,
    usp_api_UpsertDeviceReading_rollback,
)

# revision identifiers, used by Alembic.
revision = "ed909dfdb403"
down_revision = "6ff6ac15dc1a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    usp_api_UpsertDeviceReading_rollback.drop_function(op)
    usp_api_UpsertDeviceReading.create_function(op)


def downgrade() -> None:
    usp_api_UpsertDeviceReading.drop_function(op)
    usp_api_UpsertDeviceReading_rollback.create_function(op)

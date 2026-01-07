"""add-image-pairing

Revision ID: b3438a18d7f7
Revises: c8d4b455ed26
Create Date: 2025-05-29 15:05:37.924768

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b3438a18d7f7"
down_revision = "c8d4b455ed26"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE images ADD COLUMN TransmissionCaptureDateTimeUTC DateTime64 CODEC(Delta, ZSTD)"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE images DROP COLUMN TransmissionCaptureDateTimeUTC")

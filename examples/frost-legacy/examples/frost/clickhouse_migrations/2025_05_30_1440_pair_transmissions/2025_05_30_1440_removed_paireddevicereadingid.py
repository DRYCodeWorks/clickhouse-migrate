"""removed-PairedDeviceReadingID

Revision ID: fedd4b4a0c53
Revises: b3438a18d7f7
Create Date: 2025-05-30 14:40:46.345452

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "fedd4b4a0c53"
down_revision = "b3438a18d7f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE images DROP COLUMN IF EXISTS PairedDeviceReadingID")


def downgrade() -> None:
    op.execute(
        "ALTER TABLE images ADD COLUMN IF NOT EXISTS PairedDeviceReadingID UInt64 CODEC(Delta, ZSTD)"
    )

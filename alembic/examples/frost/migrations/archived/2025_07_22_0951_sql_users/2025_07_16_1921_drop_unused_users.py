"""drop-unused-users

Revision ID: 512deb64d7a1
Revises: b83a369c3353
Create Date: 2025-07-16 19:21:51.260995

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "512deb64d7a1"
down_revision = "b83a369c3353"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP USER IF EXISTS rocketwagon_luke;")
    op.execute("DROP USER IF EXISTS myradar_read;")


def downgrade() -> None:
    pass

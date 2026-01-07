"""
Base revision for ClickHouse migrations.

This is an empty revision that serves as the starting point for your
ClickHouse migration chain.

Revision ID: base_revision
Revises:
Create Date: 2025-01-01 00:00:00.000000

"""

# revision identifiers, used by Alembic.
revision = "base_revision"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Base revision - no changes needed"""
    pass


def downgrade() -> None:
    """Base revision - no changes needed"""
    pass
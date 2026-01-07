"""create_view_transmissions_full

Revision ID: 037607b704ed
Revises: c2ac8ab7728f
Create Date: 2025-08-29 14:03:48.269375

"""

from alembic import op
import sqlalchemy as sa
from helpers.utils import read_sql_file


# revision identifiers, used by Alembic.
revision = "037607b704ed"
down_revision = "c2ac8ab7728f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(read_sql_file("CreateViewTransmissionsFull", clickhouse=True))


def downgrade() -> None:
    op.execute("DROP VIEW v_transmissions_full")

"""projection

Revision ID: c0dbd7d67faa
Revises: 2db4682a61b6
Create Date: 2025-07-01 11:22:14.759057

"""

from alembic import op
import sqlalchemy as sa
from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "c0dbd7d67faa"
down_revision = "2db4682a61b6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(read_sql_file("AddSDSProjectionDedupeStrategy", clickhouse=True))
    op.execute(read_sql_file("AddSDSProjection", clickhouse=True))
    op.execute(read_sql_file("AddSDSProjectionMaterialize", clickhouse=True))


def downgrade() -> None:
    op.execute("""ALTER TABLE sds_readings DROP PROJECTION IF EXISTS proj_by_uploaded_by_rwis_id""")

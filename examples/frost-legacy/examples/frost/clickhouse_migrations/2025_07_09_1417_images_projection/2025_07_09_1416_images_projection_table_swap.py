"""images-projection_table_swap

Revision ID: 044a15a21953
Revises: 68a7139af886
Create Date: 2025-07-09 14:16:32.062517

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text  # Add this import

from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "044a15a21953"
down_revision = "68a7139af886"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    sql = read_sql_file("GetLatestImageFromTempTable", clickhouse=True)
    result = conn.execute(text(sql))
    latest_image_datetime = result.scalar()
    op.execute(read_sql_file("ExchangeTables", clickhouse=True))

    op.execute(
        read_sql_file("LoadMissingImages", clickhouse=True).replace(
            "?", f"'{latest_image_datetime.isoformat()}'"
        )
    )


def downgrade() -> None:
    """
    Since we could theoretically exeucte the swap, but fail the LoadMissingImages step, I'd rather just leave this downgrade out of the migration.
    """
    ...

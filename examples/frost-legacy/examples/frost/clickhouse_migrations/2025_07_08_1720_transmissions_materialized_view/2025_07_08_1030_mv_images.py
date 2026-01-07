"""mv-images

Revision ID: 56c950cf9658
Revises: c0dbd7d67faa
Create Date: 2025-07-08 10:30:07.714748

"""

import sqlalchemy as sa
from alembic import op

from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "56c950cf9658"
down_revision = "c0dbd7d67faa"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(read_sql_file("CreateImagesMVTable", clickhouse=True))
    op.execute(read_sql_file("CreateImagesMaterializedView", clickhouse=True))
    op.execute(read_sql_file("ImagesLoadMaterializedView", clickhouse=True))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS get_latest_images;")
    op.execute("DROP TABLE IF EXISTS latest_images;")

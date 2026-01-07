"""mv-cv

Revision ID: 2bcefd93898c
Revises: 3f75c81e0daf
Create Date: 2025-07-08 10:41:45.814044

"""

import sqlalchemy as sa
from alembic import op

from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "2bcefd93898c"
down_revision = "3f75c81e0daf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(read_sql_file("CreateCVMVTable", clickhouse=True))
    op.execute(read_sql_file("CreateCVMaterializedView", clickhouse=True))
    op.execute(read_sql_file("CVLoadMaterializedView", clickhouse=True))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS get_latest_cv_images;")
    op.execute("DROP TABLE IF EXISTS latest_cv_images;")

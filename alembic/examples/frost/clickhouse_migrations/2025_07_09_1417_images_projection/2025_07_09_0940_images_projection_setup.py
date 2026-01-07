"""images-projection

Revision ID: 68a7139af886
Revises: 597ef3808eba
Create Date: 2025-07-09 09:40:10.969316

"""

import sqlalchemy as sa
from alembic import op

from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "68a7139af886"
down_revision = "597ef3808eba"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(read_sql_file("CreateTempImagesTableWProjection", clickhouse=True))
    op.execute(read_sql_file("MigrateImagesTable", clickhouse=True))


def downgrade() -> None:
    op.execute(read_sql_file("DropTempTable", clickhouse=True))

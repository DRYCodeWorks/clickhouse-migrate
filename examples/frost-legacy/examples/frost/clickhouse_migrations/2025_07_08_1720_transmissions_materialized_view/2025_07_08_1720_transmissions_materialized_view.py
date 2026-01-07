"""transmissions-materialized-view

Revision ID: 597ef3808eba
Revises: 2bcefd93898c
Create Date: 2025-07-08 17:20:11.339076

"""

import sqlalchemy as sa
from alembic import op

from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "597ef3808eba"
down_revision = "2bcefd93898c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(read_sql_file("CreateTransmissionsMVTable", clickhouse=True))
    op.execute(read_sql_file("CreateTransmissionsMaterializedView", clickhouse=True))
    op.execute(read_sql_file("TransmissionsPairLoadMaterializedView", clickhouse=True))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS pair_transmissions_to_latest_images;")
    op.execute("DROP TABLE IF EXISTS paired_latest_image_transmissions;")

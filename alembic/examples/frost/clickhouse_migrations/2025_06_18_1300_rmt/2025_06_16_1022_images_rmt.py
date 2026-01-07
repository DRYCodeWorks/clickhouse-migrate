"""images-rmt

Revision ID: 7589cf670bae
Revises: fedd4b4a0c53
Create Date: 2025-06-16 10:22:27.241928

"""
import sqlalchemy as sa
from alembic import op

from helpers.utils import read_sql_file



# revision identifiers, used by Alembic.
revision = "7589cf670bae"
down_revision = "fedd4b4a0c53"
branch_labels = None
depends_on = None


def upgrade() -> None:
    data = read_sql_file("CreateImagesRMT", clickhouse=True)
    op.execute(data)


def downgrade() -> None:
    op.drop_table("images_rmt")


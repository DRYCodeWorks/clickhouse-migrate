"""rename-images

Revision ID: fa48d536e9e4
Revises: 00dbe665d96f
Create Date: 2025-06-18 12:48:32.772880

"""

import sqlalchemy as sa
from alembic import op

from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "fa48d536e9e4"
down_revision = "00dbe665d96f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP TABLE IF EXISTS images")
    op.execute("RENAME TABLE images_rmt TO images")


def downgrade() -> None:
    # Rename the table back to images
    op.execute("RENAME TABLE images TO images_rmt")
    op.execute(read_sql_file("CreateImages", clickhouse=True))

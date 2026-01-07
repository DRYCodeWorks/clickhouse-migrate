"""sds_calibration_update_permissions

Revision ID: cb0adfe9fe6a
Revises: 6b43e5bd681e
Create Date: 2025-08-11 13:16:11.442864

"""

import sqlalchemy as sa
from alembic import op

from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "cb0adfe9fe6a"
down_revision = "6100afb68bd2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(read_sql_file("users/SDSCalibrationTableGrantUpdate"))


def downgrade() -> None:
    op.execute(read_sql_file("users/SDSCalibrationTableRevokeUpdate"))

"""snow_depth_calibration_table_permissions

Revision ID: 6100afb68bd2
Revises: 2f080e5602a9
Create Date: 2025-08-07 12:27:08.362651

"""

import sqlalchemy as sa
from alembic import op

from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "6100afb68bd2"
down_revision = "a4041861a021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(read_sql_file("users/SDSCalibrationTableGrant"))


def downgrade() -> None:
    op.execute(read_sql_file("users/SDSCalibrationTableRevoke"))

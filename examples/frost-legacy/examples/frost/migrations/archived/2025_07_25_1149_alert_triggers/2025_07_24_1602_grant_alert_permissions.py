"""grant_alert_permissions

Revision ID: f30749fa00f9
Revises: 70f1e4be0d45
Create Date: 2025-07-24 16:02:24.710609

"""

from alembic import op
import sqlalchemy as sa
from helpers.utils import read_sql_file


# revision identifiers, used by Alembic.
revision = "f30749fa00f9"
down_revision = "70f1e4be0d45"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(read_sql_file("users/AlterAlertEngineRole_2025_07_22"))


def downgrade() -> None:
    op.execute(read_sql_file("users/AlterAlertEngineRoleRevoke_2025_07_22"))

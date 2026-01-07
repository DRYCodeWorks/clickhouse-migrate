"""device_portal_alert_triggers_permissions

Revision ID: 09edc47062eb
Revises: f30749fa00f9
Create Date: 2025-07-25 11:49:01.579360

"""

from alembic import op
import sqlalchemy as sa
from helpers.utils import read_sql_file


# revision identifiers, used by Alembic.
revision = "09edc47062eb"
down_revision = "f30749fa00f9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(read_sql_file("users/AlterDevicePortalRole_2025_07_25"))


def downgrade() -> None:
    op.execute(read_sql_file("users/AlterDevicePortalRoleRevoke_2025_07_25"))

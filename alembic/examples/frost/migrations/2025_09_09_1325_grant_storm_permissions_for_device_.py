"""grant_storm_permissions_for_device_portal

Revision ID: 03e84ddb25fb
Revises: 54281435490a
Create Date: 2025-09-09 13:25:24.201223

"""

from alembic import op
import sqlalchemy as sa
import logging

# revision identifiers, used by Alembic.
revision = "03e84ddb25fb"
down_revision = "54281435490a"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)
tables = ["StormType", "StormStatus", "StormDefinitionType"]


def upgrade() -> None:
    """Grant permissions on Storm Events tables to device_portal_api role"""

    # Grant permissions on main tables
    for table in tables:
        op.execute(
            f"""
            GRANT SELECT ON dbo.{table} TO [device_portal_api]
        """
        )
        logger.info(f"Granted permissions on {table} table")


def downgrade() -> None:
    """Revoke permissions from device_portal_api role"""

    # Revoke permissions
    for table in tables:
        try:
            op.execute(
                f"""
                REVOKE SELECT ON dbo.{table} FROM [device_portal_api]
            """
            )
            logger.info(f"Revoked permissions on {table} table")
        except Exception as e:
            logger.warning(f"Could not revoke permissions on {table}: {str(e)}")

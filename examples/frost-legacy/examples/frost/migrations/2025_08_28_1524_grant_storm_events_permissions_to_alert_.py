"""grant_storm_events_permissions_to_alert_engine

Revision ID: 32f486755bfb
Revises: a8f2c3d4e5b6
Create Date: 2025-08-28 15:24:58.275219

"""

from alembic import op
import sqlalchemy as sa
import logging

# revision identifiers, used by Alembic.
revision = "32f486755bfb"
down_revision = "a8f2c3d4e5b6"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)

tables = [
    "StormEvents",
    "StormThresholds",
]


def upgrade() -> None:
    """Grant permissions on Storm Events tables to frost_alerts_role role"""

    # Grant permissions on main tables
    for table in tables:
        op.execute(
            f"""
            GRANT SELECT, UPDATE ON dbo.{table} TO [frost_alerts_role]
        """
        )
        logger.info(f"Granted permissions on {table} table")


def downgrade() -> None:
    """Revoke permissions from frost_alerts_role role"""

    # Revoke permissions
    for table in tables:
        try:
            op.execute(
                f"""
                REVOKE SELECT, UPDATE ON dbo.{table} FROM [frost_alerts_role]
            """
            )
            logger.info(f"Revoked permissions on {table} table")
        except Exception as e:
            logger.warning(f"Could not revoke permissions on {table}: {str(e)}")

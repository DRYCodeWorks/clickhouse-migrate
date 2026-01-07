"""grant_storm_table_permissions

Revision ID: 7c77c4f44629
Revises: 0811cc2b9d7b
Create Date: 2025-09-04 12:19:58.020563

"""

from alembic import op
import sqlalchemy as sa
import logging

# revision identifiers, used by Alembic.
revision = "7c77c4f44629"
down_revision = "0811cc2b9d7b"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)

tables = ["StormType", "StormStatus", "StormDefinitionType"]


def upgrade() -> None:
    """Grant permissions on Storm Events tables to frost_alerts_role role"""

    # Grant permissions on main tables
    for table in tables:
        op.execute(
            f"""
            GRANT SELECT ON dbo.{table} TO [frost_alerts_role]
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
                REVOKE SELECT ON dbo.{table} FROM [frost_alerts_role]
            """
            )
            logger.info(f"Revoked permissions on {table} table")
        except Exception as e:
            logger.warning(f"Could not revoke permissions on {table}: {str(e)}")

"""grant storm events permissions to device_portal_api role

Revision ID: a8f2c3d4e5b6
Revises: dcac1ec2177d
Create Date: 2025-08-15 19:20:00.000000

"""

import logging

from alembic import op

# revision identifiers, used by Alembic.
revision = "a8f2c3d4e5b6"
down_revision = "dcac1ec2177d"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)

tables = [
        'StormEvents',
        'StormThresholds',
    ]

def upgrade() -> None:
    """Grant permissions on Storm Events tables to device_portal_api role"""
    
    # Grant permissions on main tables   
    for table in tables:
        op.execute(f"""
            GRANT SELECT, UPDATE ON dbo.{table} TO [device_portal_api]
        """)
        logger.info(f"Granted permissions on {table} table")
    


def downgrade() -> None:
    """Revoke permissions from device-portal-api role"""

    # Revoke permissions
    for table in tables:
        try:
            op.execute(f"""
                REVOKE SELECT, UPDATE ON dbo.{table} FROM [device_portal_api]
            """)
            logger.info(f"Revoked permissions on {table} table")
        except Exception as e:
            logger.warning(f"Could not revoke permissions on {table}: {str(e)}")
    
    
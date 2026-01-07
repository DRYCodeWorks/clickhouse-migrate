"""add-sensor-hardware

Revision ID: b955b3ad0757
Revises: a9a9a8630815
Create Date: 2025-02-26 14:30:05.076966

"""

import sqlalchemy as sa
from alembic import op

from schemas.schema import SensorHardware
from seeds.sensor_hardware import (
    NEW_SENSOR_HARDWARE_COMPONENTS,
    SENSOR_HARDWARE_COMPONENTS,
)

# revision identifiers, used by Alembic.
revision = "b955b3ad0757"
down_revision = "a9a9a8630815"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = sa.orm.Session(bind=op.get_bind())
    all_hardware = {hw.VendorID for hw in session.query(SensorHardware).all()}
    for hw in SENSOR_HARDWARE_COMPONENTS:
        if hw.VendorID not in all_hardware:
            session.add(hw)
    session.commit()


def downgrade() -> None:
    session = sa.orm.Session(bind=op.get_bind())
    for hw in NEW_SENSOR_HARDWARE_COMPONENTS:
        session.query(SensorHardware).filter(
            SensorHardware.VendorID == hw.VendorID
        ).delete()
    session.commit()

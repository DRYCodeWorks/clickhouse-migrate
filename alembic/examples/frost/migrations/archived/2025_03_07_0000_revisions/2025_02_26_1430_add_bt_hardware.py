"""add-bt-hardware

Revision ID: 13448daa34e0
Revises: b955b3ad0757
Create Date: 2025-02-26 14:30:11.719064

"""

import sqlalchemy as sa
from alembic import op

from schemas.schema import BluetoothHardware
from seeds.bluetooth_hardware import (
    BLUETOOTH_HARDWARE_COMPONENTS,
    NEW_BLUETOOTH_HARDWARE_COMPONENTS,
)

# revision identifiers, used by Alembic.
revision = "13448daa34e0"
down_revision = "b955b3ad0757"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = sa.orm.Session(bind=op.get_bind())
    all_hardware = {hw.VendorID for hw in session.query(BluetoothHardware).all()}
    for hw in BLUETOOTH_HARDWARE_COMPONENTS:
        if hw.VendorID not in all_hardware:
            session.add(hw)
    session.commit()


def downgrade() -> None:
    session = sa.orm.Session(bind=op.get_bind())
    for hw in NEW_BLUETOOTH_HARDWARE_COMPONENTS:
        session.query(BluetoothHardware).filter(
            BluetoothHardware.VendorID == hw.VendorID
        ).delete()
    session.commit()

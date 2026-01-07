"""normalize_revisions3

Revision ID: b7df821a5abd
Revises: 764bdfc890ae
Create Date: 2024-08-30 13:29:00.190437

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b7df821a5abd"
down_revision = "764bdfc890ae"
branch_labels = None
depends_on = None
from schemas.schema import (
    FrostDeviceRevisions,
    BluetoothHardware,
    SensorHardware,
)


def upgrade() -> None:
    session = sa.orm.Session(op.get_bind())
    session.query(BluetoothHardware).delete()
    op.alter_column("BluetoothHardware", "VendorID", unique=True)
    op.alter_column("SensorHardware", "VendorID", unique=True)
    s_hardware = SensorHardware(VendorID="MB7384-1")
    b_hardware = BluetoothHardware(VendorID="FRO-4-0003-R1")

    session.add(s_hardware)
    session.add(b_hardware)
    session.commit()
    f_revisions = [
        FrostDeviceRevisions(
            Name="RWIS 1.0",
        ),
        FrostDeviceRevisions(Name="RWIS 1.1"),
        FrostDeviceRevisions(Name="RWIS 1.2"),
        FrostDeviceRevisions(Name="RWIS 1.3"),
        FrostDeviceRevisions(Name="RWIS 1.4"),
        FrostDeviceRevisions(Name="RWIS 1.5"),
        FrostDeviceRevisions(Name="RWIS 1.6"),
        FrostDeviceRevisions(Name="RWIS 2.0"),
        FrostDeviceRevisions(Name="RWIS 2.1"),
        FrostDeviceRevisions(Name="FVC 1.0"),
        FrostDeviceRevisions(Name="FVC 1.0-I"),
        FrostDeviceRevisions(Name="FVC 1.1"),
        FrostDeviceRevisions(Name="FVC 1.1-I"),
        FrostDeviceRevisions(
            Name="SDS 1.0",
            BluetoothHardwareID=b_hardware.ID,
            SensorHardwareID=s_hardware.ID,
        ),
    ]
    for f in f_revisions:
        session.add(f)
    session.commit()


def downgrade() -> None:
    session = sa.orm.Session(op.get_bind())
    session.query(FrostDeviceRevisions).delete()
    session.query(SensorHardware).delete()
    session.query(BluetoothHardware).delete()

"""assign_revision

Revision ID: 26c102a4eeb8
Revises: 7df85426e98c
Create Date: 2024-08-30 14:37:36.046546

"""

import sqlalchemy as sa
from alembic import op

from schemas.schema import Devices, DeviceType, FrostDeviceRevisions

# revision identifiers, used by Alembic.
revision = "26c102a4eeb8"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = sa.orm.Session(op.get_bind())
    devices = (
        session.query(Devices)
        .filter(
            Devices.DeviceType
            == session.query(DeviceType)
            .filter(DeviceType.Name == "Snow Depth Sensor")
            .first()
            .ID
        )
        .all()
    )
    revision_id = (
        session.query(FrostDeviceRevisions)
        .filter(FrostDeviceRevisions.Name.startswith("SDS"))
        .first()
        .ID
    )
    for device in devices:
        device.Revision = revision_id
    session.commit()


def downgrade() -> None:
    pass

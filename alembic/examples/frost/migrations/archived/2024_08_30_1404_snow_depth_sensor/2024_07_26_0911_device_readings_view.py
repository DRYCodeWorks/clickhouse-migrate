"""device_readings_view

Revision ID: 31a26edc07da
Revises: 471ea2c58b7d
Create Date: 2024-07-26 09:11:57.059208

"""

import sqlalchemy as sa
from alembic import op

from schemas.other_objects.views import DeviceImagesView, DeviceReadingsView

# revision identifiers, used by Alembic.
revision = "31a26edc07da"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    DeviceReadingsView.create(op)
    DeviceReadingsView.define_index(op)
    DeviceImagesView.create(op)
    DeviceImagesView.define_index(op)


def downgrade() -> None:
    DeviceReadingsView.drop(op)
    DeviceImagesView.drop(op)

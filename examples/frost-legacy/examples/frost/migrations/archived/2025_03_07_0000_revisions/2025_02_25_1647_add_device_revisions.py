"""add-device-revisions

Revision ID: a9a9a8630815
Revises: 28e247d29b51
Create Date: 2025-02-25 16:47:48.204816

"""

import sqlalchemy as sa
from alembic import op

from schemas.schema import FrostDeviceRevisions
from seeds.hardware_revisions import HARDWARE_REVISIONS, NEW_HARDWARE_REVISIONS

# revision identifiers, used by Alembic.
revision = "a9a9a8630815"
down_revision = "28e247d29b51"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = sa.orm.Session(bind=op.get_bind())
    all_revisions = {
        hw_revision.Name for hw_revision in session.query(FrostDeviceRevisions).all()
    }
    for hw_revision in HARDWARE_REVISIONS:
        if hw_revision.Name not in all_revisions:
            session.add(hw_revision)
    session.commit()


def downgrade() -> None:
    session = sa.orm.Session(bind=op.get_bind())
    for hw_revision in NEW_HARDWARE_REVISIONS:
        session.query(FrostDeviceRevisions).filter(
            FrostDeviceRevisions.Name == hw_revision.Name
        ).delete()
    session.commit()

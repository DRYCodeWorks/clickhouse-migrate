"""device_lineage_initial_state

Revision ID: f6a6f779f5dd
Revises: 9c4abca82eb3
Create Date: 2023-11-01 15:35:16.999430

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f6a6f779f5dd"
down_revision = "9c4abca82eb3"
branch_labels = None
depends_on = None


from schemas.other_objects.triggers import DEVICE_INITIAL_STATE
from schemas.other_objects.groupid_change_datalineage import DEVICE_INITIAL_STATE_2


def upgrade() -> None:
    try:
        DEVICE_INITIAL_STATE.drop_trigger(op)
    except:
        # The trigger does not exist
        ...
    DEVICE_INITIAL_STATE_2.create_trigger(op)


def downgrade() -> None:
    DEVICE_INITIAL_STATE_2.drop_trigger(op)
    # This downgrade does not replace the previous trigger

"""constrain_pairing

Revision ID: 675203a95d1b
Revises: 31a26edc07da
Create Date: 2024-08-28 10:26:31.820140

"""

from alembic import op
import sqlalchemy as sa
from schemas.other_objects.check_constraints import RWIS_PAIR_CONSTRAINTS
from schemas.other_objects.functions import GET_DEVICE_TYPE_NAME


# revision identifiers, used by Alembic.
revision = "675203a95d1b"
down_revision = "31a26edc07da"
branch_labels = None
depends_on = None


constraint_name, table = RWIS_PAIR_CONSTRAINTS.name, "SnowDepthRWISPairs"


def upgrade() -> None:
    GET_DEVICE_TYPE_NAME.create_function(op)
    op.create_check_constraint(constraint_name, table, RWIS_PAIR_CONSTRAINTS.sqltext)


def downgrade() -> None:
    op.drop_constraint(f"ck_{table}_{constraint_name}", table)
    GET_DEVICE_TYPE_NAME.drop_function(op)

"""idempotent-writes-sds

Revision ID: 435b9810dd0e
Revises: cd9a9fab7cf6
Create Date: 2024-11-07 11:06:09.165428

"""

import sqlalchemy as sa
from alembic import op

from schemas.other_objects.functions import (
    usp_InsertSnowDepthReadingV3,
    usp_InsertSnowDepthReadingV4,
)

# revision identifiers, used by Alembic.
revision = "435b9810dd0e"
down_revision = "cd9a9fab7cf6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    usp_InsertSnowDepthReadingV3.drop_function(op)
    usp_InsertSnowDepthReadingV4.create_function(op)


def downgrade() -> None:
    usp_InsertSnowDepthReadingV4.drop_function(op)
    usp_InsertSnowDepthReadingV3.create_function(op)

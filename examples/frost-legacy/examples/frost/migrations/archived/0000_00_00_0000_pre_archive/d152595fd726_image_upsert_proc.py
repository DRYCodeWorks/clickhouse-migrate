"""image_upsert_proc

Revision ID: d152595fd726
Revises: ddc14f11cac7
Create Date: 2024-05-08 14:52:27.463198

"""

from alembic import op
import sqlalchemy as sa
from schemas.other_objects.functions import UpsertCompletedImageFeature


# revision identifiers, used by Alembic.
revision = "d152595fd726"
down_revision = "ddc14f11cac7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for func in UpsertCompletedImageFeature.values():
        func.create_function(op)


def downgrade() -> None:
    for func in UpsertCompletedImageFeature.values():
        func.drop_function(op)

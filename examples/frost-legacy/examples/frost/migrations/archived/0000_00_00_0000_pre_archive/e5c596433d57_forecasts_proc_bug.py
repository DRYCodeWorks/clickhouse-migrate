"""forecasts_proc_bug

Revision ID: e5c596433d57
Revises: d152595fd726
Create Date: 2024-06-05 09:47:34.481678

"""

from alembic import op
import sqlalchemy as sa
from schemas.other_objects.functions import ForecastUpsertProcV1, ForecastUpsertProcV2

# revision identifiers, used by Alembic.
revision = "e5c596433d57"
down_revision = "d152595fd726"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for func in ForecastUpsertProcV1.values():
        func.drop_function(op)
    for func in ForecastUpsertProcV2.values():
        func.create_function(op)


def downgrade() -> None:
    for func in ForecastUpsertProcV2.values():
        func.drop_function(op)
    for func in ForecastUpsertProcV1.values():
        func.create_function(op)

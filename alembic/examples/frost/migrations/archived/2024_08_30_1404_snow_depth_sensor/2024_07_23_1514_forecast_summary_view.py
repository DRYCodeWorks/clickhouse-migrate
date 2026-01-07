"""forecasts_view

Revision ID: 753144b95918
Revises: 0c651d3c3936
Create Date: 2024-07-23 15:14:36.455307

"""

import sqlalchemy as sa
from alembic import op

from schemas.other_objects.views import LatestNCARForecastsSummaryView

# revision identifiers, used by Alembic.
revision = "753144b95918"
down_revision = "0c651d3c3936"
branch_labels = None
depends_on = None


def upgrade() -> None:
    LatestNCARForecastsSummaryView.create(op)
    LatestNCARForecastsSummaryView.define_index(op)


def downgrade() -> None:
    LatestNCARForecastsSummaryView.drop(op)

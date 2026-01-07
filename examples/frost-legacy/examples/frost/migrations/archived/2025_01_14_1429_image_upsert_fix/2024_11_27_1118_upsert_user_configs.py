"""upsert-user-configs

Revision ID: 360085af62c5
Revises: 435b9810dd0e
Create Date: 2024-11-27 11:18:26.563872

"""

import sqlalchemy as sa
from alembic import op

from schemas.other_objects.functions import usp_api_UpsertUserConfigurationsGroups

# revision identifiers, used by Alembic.
revision = "360085af62c5"
down_revision = "435b9810dd0e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    usp_api_UpsertUserConfigurationsGroups.create_function(op)


def downgrade() -> None:
    usp_api_UpsertUserConfigurationsGroups.drop_function(op)

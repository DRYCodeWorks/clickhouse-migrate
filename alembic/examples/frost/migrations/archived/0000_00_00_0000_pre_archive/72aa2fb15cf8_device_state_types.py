"""
Configures the DeviceStateType table and inserts initial types.

Revision ID: 72aa2fb15cf8
Revises: 2461edb98707
Create Date: 2023-09-05 11:45:42.517486

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mssql


# revision identifiers, used by Alembic.
revision = "72aa2fb15cf8"
down_revision = "2461edb98707"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from migrations.helpers import (
        insert_device_state_types,
    )

    op.create_table(
        "DeviceStateType",
        sa.Column(
            "ID",
            sa.SmallInteger(),
            sa.Identity(always=False, start=0, increment=1),
            nullable=False,
        ),
        sa.Column("DeviceStateName", sa.String(length=12), nullable=False),
        sa.Column("Description", sa.String(length=2000), nullable=False),
        sa.Column("CreatedDateTimeUTC", mssql.DATETIME2(), nullable=True),
        sa.PrimaryKeyConstraint("ID", name=op.f("pk_DeviceStateType")),
        sa.UniqueConstraint(
            "DeviceStateName", name=op.f("uq_DeviceStateType_DeviceStateName")
        ),
    )
    insert_device_state_types(op, sa.orm)


def downgrade() -> None:
    op.drop_table("DeviceStateType")

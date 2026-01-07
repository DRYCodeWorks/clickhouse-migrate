"""add_storm_events_table

Revision ID: 42c8f57b7768
Revises: 3ed2e5937d97
Create Date: 2025-08-13 14:05:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import mssql

# revision identifiers, used by Alembic.
revision = "42c8f57b7768"
down_revision = "3ed2e5937d97"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create StormEvents table with 1-to-1 device relationship
    op.create_table(
        "StormEvents",
        sa.Column(
            "ID",
            sa.BigInteger(),
            sa.Identity(always=False, start=1, increment=1),
            nullable=False,
        ),
        sa.Column("DeviceID", sa.BigInteger(), nullable=False),
        sa.Column("StormTypeID", sa.SmallInteger(), nullable=False),
        sa.Column("StormStatusID", sa.SmallInteger(), nullable=False),
        sa.Column("TriggerSource", sa.String(50), nullable=True),
        sa.Column("TriggerMetadata", sa.String(), nullable=True),
        sa.Column("StartDateTimeUTC", mssql.DATETIME2(precision=3), nullable=False),
        sa.Column("EndDateTimeUTC", mssql.DATETIME2(precision=3), nullable=True),
        sa.Column("DefinitionTypeID", sa.SmallInteger(), nullable=False),
        sa.Column("Notes", sa.String(), nullable=True),
        sa.Column(
            "IsActive",
            sa.Boolean(),
            server_default=sa.text("((1))"),
            nullable=False,
        ),
        sa.Column(
            "CreatedDateTimeUTC",
            mssql.DATETIME2(precision=3),
            server_default=sa.text("(getutcdate())"),
            nullable=False,
        ),
        sa.Column("CreatedUserID", mssql.UNIQUEIDENTIFIER(), nullable=True),
        sa.Column("ModifiedDateTimeUTC", mssql.DATETIME2(precision=3), nullable=True),
        sa.Column("ModifiedUserID", mssql.UNIQUEIDENTIFIER(), nullable=True),
        sa.ForeignKeyConstraint(
            ["DeviceID"],
            ["Devices.ID"],
            name=op.f("fk_StormEvents_DeviceID_Devices"),
        ),
        sa.ForeignKeyConstraint(
            ["StormTypeID"],
            ["StormType.ID"],
            name=op.f("fk_StormEvents_StormTypeID_StormType"),
        ),
        sa.ForeignKeyConstraint(
            ["StormStatusID"],
            ["StormStatus.ID"],
            name=op.f("fk_StormEvents_StormStatusID_StormStatus"),
        ),
        sa.ForeignKeyConstraint(
            ["DefinitionTypeID"],
            ["StormDefinitionType.ID"],
            name=op.f("fk_StormEvents_DefinitionTypeID_StormDefinitionType"),
        ),
        sa.ForeignKeyConstraint(
            ["CreatedUserID"],
            ["Users.ID"],
            name=op.f("fk_StormEvents_CreatedUserID_Users"),
        ),
        sa.ForeignKeyConstraint(
            ["ModifiedUserID"],
            ["Users.ID"],
            name=op.f("fk_StormEvents_ModifiedUserID_Users"),
        ),
        sa.PrimaryKeyConstraint("ID", name=op.f("pk_StormEvents")),
    )

    # Create indexes for optimal querying
    op.create_index(
        "IX_StormEvents_DeviceID",
        "StormEvents",
        ["DeviceID"],
    )
    op.create_index(
        "IX_StormEvents_Dates",
        "StormEvents",
        ["StartDateTimeUTC", "EndDateTimeUTC"],
    )
    op.create_index(
        "IX_StormEvents_Status",
        "StormEvents",
        ["StormStatusID"],
    )
    op.create_index(
        "IX_StormEvents_TriggerSource",
        "StormEvents",
        ["TriggerSource"],
        mssql_where=sa.text("TriggerSource IS NOT NULL"),
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index("IX_StormEvents_TriggerSource", table_name="StormEvents")
    op.drop_index("IX_StormEvents_Status", table_name="StormEvents")
    op.drop_index("IX_StormEvents_Dates", table_name="StormEvents")
    op.drop_index("IX_StormEvents_DeviceID", table_name="StormEvents")

    # Drop table
    op.drop_table("StormEvents")

"""add_storm_enum_tables

Revision ID: 3ed2e5937d97
Revises: cb0adfe9fe6a
Create Date: 2025-08-13 14:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3ed2e5937d97"
down_revision = "cb0adfe9fe6a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create StormType enum table
    op.create_table(
        "StormType",
        sa.Column("ID", sa.SmallInteger(), nullable=False),
        sa.Column("Name", sa.String(50), nullable=False),
        sa.Column("Description", sa.String(200), nullable=True),
        sa.Column(
            "IsActive", sa.Boolean(), server_default=sa.text("((1))"), nullable=False
        ),
        sa.PrimaryKeyConstraint("ID", name=op.f("pk_StormType")),
    )

    # Create StormStatus enum table
    op.create_table(
        "StormStatus",
        sa.Column("ID", sa.SmallInteger(), nullable=False),
        sa.Column("Name", sa.String(50), nullable=False),
        sa.Column("Description", sa.String(200), nullable=True),
        sa.Column(
            "IsActive", sa.Boolean(), server_default=sa.text("((1))"), nullable=False
        ),
        sa.PrimaryKeyConstraint("ID", name=op.f("pk_StormStatus")),
    )

    # Create StormDefinitionType enum table
    op.create_table(
        "StormDefinitionType",
        sa.Column("ID", sa.SmallInteger(), nullable=False),
        sa.Column("Name", sa.String(50), nullable=False),
        sa.Column("Description", sa.String(200), nullable=True),
        sa.Column(
            "IsActive", sa.Boolean(), server_default=sa.text("((1))"), nullable=False
        ),
        sa.PrimaryKeyConstraint("ID", name=op.f("pk_StormDefinitionType")),
    )

    # Insert seed data for StormType
    op.execute("SET IDENTITY_INSERT StormType ON")
    op.execute(
        """
        INSERT INTO StormType (ID, Name, Description) VALUES
        (1, 'Winter', 'Snow/Ice storm event'),
        (2, 'Mixed', 'Could be Snow or Rain'),
        (3, 'Rain', 'Rain storm event')
    """
    )
    op.execute("SET IDENTITY_INSERT StormType OFF")

    # Insert seed data for StormStatus
    op.execute("SET IDENTITY_INSERT StormStatus ON")
    op.execute(
        """
        INSERT INTO StormStatus (ID, Name, Description) VALUES
        (1, 'Predicted', 'Storm predicted but not yet started'),
        (2, 'Active', 'Storm currently in progress'),
        (3, 'Completed', 'Storm has ended'),
        (4, 'Cancelled', 'Predicted storm did not materialize')
    """
    )
    op.execute("SET IDENTITY_INSERT StormStatus OFF")

    # Insert seed data for StormDefinitionType
    op.execute("SET IDENTITY_INSERT StormDefinitionType ON")
    op.execute(
        """
        INSERT INTO StormDefinitionType (ID, Name, Description) VALUES
        (1, 'UserDefined', 'Defined by user'),
        (2, 'AutoDetected', 'Automatically detected by system'),
        (3, 'Retroactive', 'Defined after the fact')
    """
    )
    op.execute("SET IDENTITY_INSERT StormDefinitionType OFF")


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("StormDefinitionType")
    op.drop_table("StormStatus")
    op.drop_table("StormType")
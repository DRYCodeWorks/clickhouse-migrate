"""check_constraint_provisioning_group_id

Revision ID: 1aca50f1f41f
Revises: a1fd842b0ccb
Create Date: 2023-09-05 11:46:42.293217

"""
from alembic import op

import sqlalchemy as sa
from schemas.other_objects.check_constraints import (
    provisioning_group_for_proper_device_states,
    DEVICES_TABLE_CONSTRAINTS,
)


# revision identifiers, used by Alembic.
revision = "1aca50f1f41f"
down_revision = "a1fd842b0ccb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    session = sa.orm.Session(bind=op.get_bind())
    deprecated_id = session.execute(
        "SELECT ID FROM DeviceStateType WHERE DeviceStateName = 'Deprecated'"
    ).fetchone()[0]
    provisioned_id = session.execute(
        "SELECT ID FROM DeviceStateType WHERE DeviceStateName = 'Provisioned'"
    ).fetchone()[0]

    try:
        provisioning_group_id = session.execute(
            "SELECT GroupID FROM Groups WHERE Name = 'PROVISIONING_GROUP'"
        ).fetchone()[0]
    except:
        raise Exception("Must declare a provisioning group before running this script")

    check_constraint = provisioning_group_for_proper_device_states(
        provisioning_group_id, deprecated_id, provisioned_id
    )
    constraint_name, table = check_constraint.name, "Devices"
    op.drop_constraint("ck_Devices_groupid_assigned_for_proper_device_states", table)
    op.create_check_constraint(constraint_name, table, check_constraint.sqltext)
    session.commit()


def downgrade() -> None:
    session = sa.orm.Session(bind=op.get_bind())
    check_constraint = DEVICES_TABLE_CONSTRAINTS[1]
    constraint_name, table = check_constraint.name, "Devices"
    op.drop_constraint(
        "ck_Devices_provisioning_group_for_proper_device_states", "Devices"
    )
    op.create_check_constraint(constraint_name, table, check_constraint.sqltext)
    session.commit()

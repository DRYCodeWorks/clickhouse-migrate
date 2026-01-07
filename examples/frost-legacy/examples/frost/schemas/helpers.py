from sqlalchemy.orm import Session

from schemas.check_constraints import DEVICES_TABLE_CONSTRAINTS
from schemas.schema import Devices, DeviceState, DeviceType
from seeds.device_state import DEVICE_STATES
from seeds.device_type import DEVICE_TYPES
from seeds.hardware_revisions import HARDWARE_REVISIONS


def insert_device_state_types(op, orm):
    session = orm.Session(bind=op.get_bind())
    session.add_all(DEVICE_STATES)
    session.commit()


def insert_device_state_constraints(op):
    for check_constraint in DEVICES_TABLE_CONSTRAINTS:
        constraint_name, table = check_constraint.name, check_constraint.table
        op.create_check_constraint(constraint_name, table, check_constraint.sqltext)


def drop_device_state_constraints(op):
    for check_constraint in DEVICES_TABLE_CONSTRAINTS:
        constraint_name, table = check_constraint.name, check_constraint.table
        op.drop_constraint(constraint_name, table)


def insert_sample_models(op, orm, models):
    session = orm.Session(
        bind=op.get_bind(),
    )
    session.add_all(models)
    session.commit()


def drop_sample_models(op, orm, models): ...


def set_default_device_state(
    op,
    orm,
):
    session: Session = orm.Session(bind=op.get_bind())
    activated = (
        session.query(DeviceState)
        .filter(DeviceState.DeviceStateName == "Activated")
        .first()
    )
    registered = (
        session.query(DeviceState)
        .filter(DeviceState.DeviceStateName == "Registered")
        .first()
    )
    devices = session.query(Devices).all()
    for device in devices:
        if device.IsActive:
            device.DeviceState = activated.ID
        else:
            device.DeviceState = registered.ID
    session.commit()


def insert_device_types(op, orm):
    session = orm.Session(bind=op.get_bind())
    session.add_all(DEVICE_TYPES)
    session.commit()


def set_default_device_type(op, orm):
    session: Session = orm.Session(bind=op.get_bind())
    mini_rwis = session.query(DeviceType).filter(DeviceType.Name == "Mini RWIS").first()
    devices = session.query(Devices).all()
    for device in devices:
        device.DeviceType = mini_rwis.ID
    session.commit()


def insert_revisions(op, orm):
    session = orm.Session(bind=op.get_bind())
    session.add_all(HARDWARE_REVISIONS)
    session.add_all(BLUETOOTH_REVISIONS)
    session.commit()

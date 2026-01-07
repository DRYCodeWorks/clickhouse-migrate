from sqlalchemy import CheckConstraint


def provisioning_group_for_proper_device_states(
    provisioning_group_id, deprecated_id=2, provisioned_id=3
):
    return CheckConstraint(
        f"(DeviceState in ({deprecated_id}, {provisioned_id}) AND GroupId = {provisioning_group_id}) OR GroupId != {provisioning_group_id}",
        name="provisioning_group_for_proper_device_states",
    )


DEVICES_TABLE_CONSTRAINTS = (
    CheckConstraint(
        f"(DeviceState = 0 AND (IsActive = 1) OR (DeviceState != 0 AND (IsActive = 0)))",
        name="activated_matches_device_state",
    ),
    CheckConstraint(
        f"(DeviceState <= 1 AND (GroupId IS NOT NULL) OR (DeviceState > 1 AND GroupID IS NULL))",
        name="groupid_assigned_for_proper_device_states",
    ),
)


RWIS_PAIR_CONSTRAINTS = CheckConstraint(
    f"""dbo.get_device_type_name(RWISDeviceID) = 'Mini RWIS' 
    AND dbo.get_device_type_name(SnowDepthDeviceID) = 'Snow Depth Sensor'""",
    name="rwis_pair_device_types",
)

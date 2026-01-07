from schemas.schema import DeviceState

DEVICE_STATES = [
    DeviceState(
        DeviceStateName="Activated",
        Description="A device which is currently registered to a Frost customer, and which is visible in the customer portal",
    ),
    DeviceState(
        DeviceStateName="Registered",
        Description="A device which is currently registered to a Frost customer, but has yet to be activated in the customer portal",
    ),
    DeviceState(
        DeviceStateName="Deprecated",
        Description="A device which was previously registered to a customer, and has been mailed back to Frost ops for refurbishment.",
    ),
    DeviceState(
        DeviceStateName="Provisioned",
        Description="A device which has been added to the Devices table, assigned a customer `GroupID` by Frost administrators, but has yet to be registered to a Frost customer. ",
    ),
    DeviceState(
        DeviceStateName="Assigned",
        Description="A device which has been provisioned AND given a GroupID associated with a customer, but has yet to be registered to the fleet by the Frost customer.",
    ),
]

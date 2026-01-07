from schemas.schema import StormType, StormStatus, StormDefinitionType

STORM_TYPES = [
    StormType(ID=1, Name="Winter", Description="Snow/Ice storm event"),
    StormType(ID=2, Name="Mixed", Description="Could be Snow or Rain"),
    StormType(ID=3, Name="Rain", Description="Rain storm event"),
]

STORM_STATUSES = [
    StormStatus(ID=1, Name="Predicted", Description="Storm predicted but not yet started"),
    StormStatus(ID=2, Name="Active", Description="Storm currently in progress"),
    StormStatus(ID=3, Name="Completed", Description="Storm has ended"),
    StormStatus(ID=4, Name="Cancelled", Description="Predicted storm did not materialize"),
]

STORM_DEFINITION_TYPES = [
    StormDefinitionType(ID=1, Name="UserDefined", Description="Defined by user"),
    StormDefinitionType(ID=2, Name="AutoDetected", Description="Automatically detected by system"),
    StormDefinitionType(ID=3, Name="Retroactive", Description="Defined after the fact"),
]
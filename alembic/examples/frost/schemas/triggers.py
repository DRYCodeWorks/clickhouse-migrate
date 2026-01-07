from sqlalchemy import Table
from schemas.schema import Devices, DeviceLineage, GroupsMixin


class Trigger:
    def __init__(self, name, sqltext, table: Table):
        self.name = name
        self.sqltext = sqltext
        self.table = table.__tablename__

    def _render(self):
        return self.sqltext.format(name=self.name, table=self.table)

    def create_trigger(self, op):
        op.execute(
            f"CREATE TRIGGER [dbo].[trg_{self.name}] ON [dbo].[{self.table}] {self._render()}"
        )
        op.execute(f"ALTER TABLE [dbo].[{self.table}] ENABLE TRIGGER [trg_{self.name}]")

    def drop_trigger(self, op):
        op.execute(f"DROP TRIGGER [trg_{self.name}]")


ADD_GROUP_CHANGE_TO_DEVICE_LINEAGE = Trigger(
    "LogStateChanges",
    """
    AFTER UPDATE
    AS
    BEGIN
        IF UPDATE(DeviceState) OR Update(GroupID) OR Update(VendorDeviceId)
        BEGIN
            INSERT INTO DeviceLineage(
                DeviceID,
                OldGroupID,
                OldDeviceState,
                OldVendorDeviceId,
                NewGroupID,
                NewDeviceState,
                NewVendorDeviceId,
                CreatedDateTimeUTC
            )
            SELECT 
                OLD.ID, 
                OLD.GroupID, 
                OLD.DeviceState as PrevState,
                Old.VendorDeviceId,
                NEW.GroupID,
                NEW.DeviceState as NewState, 
                New.VendorDeviceId,
                GETDATE()
            FROM
                inserted as NEW
            JOIN deleted OLD ON NEW.ID = OLD.ID         
        END;
    END;    
    """,
    Devices,
)
DEVICE_STATE_CHANGE = Trigger(
    "LogStateChanges",
    """
    AFTER UPDATE
    AS
    BEGIN
        IF UPDATE(DeviceState)
        BEGIN
            INSERT INTO DeviceLineage(
                DeviceID,
                GroupId,
                OldDeviceState,
                NewDeviceState,
                VendorDeviceId,
                CreatedDateTimeUTC
            )
            SELECT 
                OLD.ID, 
                OLD.GroupID, 
                OLD.DeviceState as PrevState,
                NEW.DeviceState as NewState, 
                OLD.VendorDeviceId,
                GETDATE()
            FROM
                inserted as NEW
            JOIN deleted OLD ON NEW.ID = OLD.ID         
        END;
    END;    
    """,
    Devices,
)

DEVICE_INITIAL_STATE = Trigger(
    "LogInitialState",
    """
    AFTER INSERT
        AS
        BEGIN
            INSERT INTO DeviceLineage(
                DeviceID,
                GroupId,
                OldDeviceState,
                NewDeviceState,
                VendorDeviceId,
                CreatedDateTimeUTC
            )
            SELECT 
                ID, 
                GroupID, 
                NULL,
                DeviceState as NewState, 
                VendorDeviceId,
                GETDATE()
            FROM
                inserted
        END;    
    """,
    Devices,
)

ENFORCE_TIMEOUT_ON_EXPECTING_REPLACEMENTS = Trigger(
    "EnforceTimeoutOnExpectingReplacements",
    """
    AFTER INSERT, UPDATE
        AS
            BEGIN
                IF EXISTS (SELECT * FROM Groups WHERE ExpectReplacementDevicesTimeout < GETDATE())
                UPDATE Groups SET ExpectReplacementDevices = 0
            WHERE ExpectReplacementDevicesTimeout < GETDATE()
    END;
    """,
    GroupsMixin,
)

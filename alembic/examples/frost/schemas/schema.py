"""
The shared schema file is intended to store all the common objects across ALL database environments. As such,
it has the responsibility of orchestrating several other shared tasks, such as naming indexes and initializing
SQL alchemy metadata.

Only objects which will be shared in every iteration of the database should be added here. Models which will be shared
by some but not all environments should be added to the `shared_models` directory.
"""

import enum

from sqlalchemy import (
    DECIMAL,
    JSON,
    REAL,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Index,
    Integer,
    PrimaryKeyConstraint,
    SmallInteger,
    String,
    Table,
    Time,
    Unicode,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.mssql import DATETIME2, TINYINT, UNIQUEIDENTIFIER
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import column_property, declarative_base, relationship
from sqlalchemy.sql import func

from schemas.check_constraints import DEVICES_TABLE_CONSTRAINTS

Base = declarative_base()
metadata = Base.metadata
metadata.naming_convention = {
    "ix": "%(column_0_label)s_IX",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class CustomSettings(Base):
    __tablename__ = "CustomSettings"

    ID = Column(BigInteger, Identity(start=1, increment=1), nullable=False)
    SettingCode = Column(String(200, "SQL_Latin1_General_CP1_CI_AS"), primary_key=True)
    SettingValue = Column(String(5000, "SQL_Latin1_General_CP1_CI_AS"), nullable=False)
    Description = Column(String(5000, "SQL_Latin1_General_CP1_CI_AS"), nullable=False)


t_DebugLog = Table(
    "DebugLog",
    metadata,
    Column("ID", BigInteger, Identity(start=1, increment=1), nullable=False),
    Column("SourceName", String(100, "SQL_Latin1_General_CP1_CI_AS"), nullable=False),
    Column("SourceKey", String(100, "SQL_Latin1_General_CP1_CI_AS")),
    Column("ErrorCode", Integer),
    Column("ErrorMessage", String(5000, "SQL_Latin1_General_CP1_CI_AS")),
    Column("DebugData", String(collation="SQL_Latin1_General_CP1_CI_AS")),
    Column("CreatedDateTimeUTC", DateTime, nullable=False),
    Index(
        "IDX_DebugLog_SourceName_SourceKey_CreateDate",
        "SourceName",
        "SourceKey",
        "CreatedDateTimeUTC",
    ),
)


class LocationType(Base):
    __tablename__ = "LocationType"

    ID = Column(SmallInteger, Identity(start=1, increment=1), primary_key=True)
    Name = Column(String(50, "SQL_Latin1_General_CP1_CI_AS"), nullable=False)
    IsActive = Column(Boolean, nullable=False, server_default=text("((1))"))

    Devices = relationship("Devices", back_populates="LocationType")


class NotificationMethod(Base):
    __tablename__ = "NotificationMethod"

    ID = Column(SmallInteger, nullable=False)
    Name = Column(String(30, "SQL_Latin1_General_CP1_CI_AS"), primary_key=True)
    Description = Column(String(1000, "SQL_Latin1_General_CP1_CI_AS"), nullable=False)
    CreateDateTimeUTC = Column(
        DateTime, nullable=False, server_default=text("(getdate())")
    )


class NotificationReferenceType(Base):
    __tablename__ = "NotificationReferenceType"

    ID = Column(SmallInteger, nullable=False)
    Name = Column(String(30, "SQL_Latin1_General_CP1_CI_AS"), primary_key=True)
    Description = Column(String(1000, "SQL_Latin1_General_CP1_CI_AS"), nullable=False)
    CreateDateTimeUTC = Column(
        DateTime, nullable=False, server_default=text("(getdate())")
    )


class NotificationStatus(Base):
    __tablename__ = "NotificationStatus"

    ID = Column(SmallInteger, nullable=False)
    Name = Column(String(30, "SQL_Latin1_General_CP1_CI_AS"), primary_key=True)
    Description = Column(String(1000, "SQL_Latin1_General_CP1_CI_AS"), nullable=False)
    CreateDateTimeUTC = Column(
        DateTime, nullable=False, server_default=text("(getdate())")
    )


class NotificationType(Base):
    __tablename__ = "NotificationType"

    ID = Column(SmallInteger, nullable=False)
    Name = Column(String(30, "SQL_Latin1_General_CP1_CI_AS"), primary_key=True)
    Description = Column(String(1000, "SQL_Latin1_General_CP1_CI_AS"), nullable=False)
    CreateDateTimeUTC = Column(
        DateTime, nullable=False, server_default=text("(getdate())")
    )


class Notifications(Base):
    __tablename__ = "Notifications"
    __table_args__ = (
        Index(
            "IDX_Notifications_Method_Type_Status_NotifyDateTimeUTC",
            "NotificationMethodID",
            "NotificationTypeID",
            "NotificationStatusID",
            "NotifyDateTimeUTC",
        ),
    )

    ID = Column(BigInteger, Identity(start=1, increment=1), primary_key=True)
    DeviceID = Column(BigInteger, nullable=False)
    NotificationMethodID = Column(SmallInteger, nullable=False)
    NotificationTypeID = Column(SmallInteger, nullable=False)
    NotificationStatusID = Column(SmallInteger, nullable=False)
    CreateDateTimeUTC = Column(DateTime, nullable=False)
    ReferenceTypeID = Column(SmallInteger)
    ReferenceKey = Column(String(50, "SQL_Latin1_General_CP1_CI_AS"))
    NotifyDateTimeUTC = Column(DateTime)
    SentDateTimeUTC = Column(DateTime)
    Data = Column(String(8000, "SQL_Latin1_General_CP1_CI_AS"))
    TriggeredUserID = Column(UNIQUEIDENTIFIER)


class RequestType(Base):
    __tablename__ = "RequestType"

    ID = Column(Integer, Identity(start=1, increment=1), nullable=False)
    RequestTypeCode = Column(
        String(30, "SQL_Latin1_General_CP1_CI_AS"), primary_key=True
    )
    Description = Column(String(2000, "SQL_Latin1_General_CP1_CI_AS"), nullable=False)
    CreateDateTimeUTC = Column(DateTime, nullable=False)
    DisplayName = Column(String(100, "SQL_Latin1_General_CP1_CI_AS"))

    DeviceRequests = relationship("DeviceRequests", back_populates="RequestType")


class SurfaceType(Base):
    __tablename__ = "SurfaceType"

    ID = Column(SmallInteger, Identity(start=1, increment=1), primary_key=True)
    Name = Column(String(50, "SQL_Latin1_General_CP1_CI_AS"), nullable=False)
    IsActive = Column(Boolean, nullable=False, server_default=text("((1))"))

    Devices = relationship("Devices", back_populates="SurfaceType")


class TaskReferenceType(Base):
    __tablename__ = "TaskReferenceType"

    ID = Column(Integer, nullable=False)
    Name = Column(String(30, "SQL_Latin1_General_CP1_CI_AS"), primary_key=True)
    Description = Column(String(1000, "SQL_Latin1_General_CP1_CI_AS"), nullable=False)
    CreateDateTimeUTC = Column(DateTime, nullable=False)


t_TaskStatus = Table(
    "TaskStatus",
    metadata,
    Column("ID", Integer, nullable=False),
    Column("Name", String(30, "SQL_Latin1_General_CP1_CI_AS"), nullable=False),
    Column("Description", String(1000, "SQL_Latin1_General_CP1_CI_AS"), nullable=False),
    Column("CreateDateTimeUTC", DateTime, nullable=False),
)


class TaskType(Base):
    __tablename__ = "TaskType"

    ID = Column(Integer, nullable=False)
    Name = Column(String(30, "SQL_Latin1_General_CP1_CI_AS"), primary_key=True)
    Description = Column(String(1000, "SQL_Latin1_General_CP1_CI_AS"), nullable=False)
    CreateDateTimeUTC = Column(DateTime, nullable=False)


class Tasks(Base):
    __tablename__ = "Tasks"

    ID = Column(BigInteger, Identity(start=1, increment=1), primary_key=True)
    TaskTypeID = Column(SmallInteger, nullable=False)
    TaskStatusID = Column(SmallInteger, nullable=False)
    CreateDateTimeUTC = Column(DateTime, nullable=False)
    DeviceID = Column(BigInteger)
    ReferenceTypeID = Column(SmallInteger)
    ReferenceKey = Column(String(50, "SQL_Latin1_General_CP1_CI_AS"))
    ProcessedDateTimeUTC = Column(DateTime)
    Data = Column(String(8000, "SQL_Latin1_General_CP1_CI_AS"))
    DebugInfo = Column(String(8000, "SQL_Latin1_General_CP1_CI_AS"))
    LockDateTimeUTC = Column(DateTime)
    LockBy = Column(String(30, "SQL_Latin1_General_CP1_CI_AS"))
    ModifiedDateTimeUTC = Column(DateTime)
    ModifiedByUserName = Column(String(30, "SQL_Latin1_General_CP1_CI_AS"))


class UserDevices(Base):
    __tablename__ = "UserDevices"

    UserGroupID = Column(UNIQUEIDENTIFIER, primary_key=True, nullable=False)
    DeviceID = Column(BigInteger, primary_key=True, nullable=False)
    Permission = Column(SmallInteger, nullable=False)


class UserConfigurations(Base):
    __tablename__ = "UserConfigurations"

    UserID = Column(ForeignKey("Users.ID"), primary_key=True, nullable=False)
    DefaultViewGroupID = Column(ForeignKey("Groups.GroupID"), nullable=True)
    EmployedAtGroupID = Column(ForeignKey("Groups.GroupID"), nullable=True)
    ForecastIntervalHours = Column(TINYINT, nullable=False, default=72)


class UsersMixin:
    __tablename__ = "Users"

    ID = Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("(newid())"))
    FirstName = Column(Unicode(100), nullable=False, index=True)
    LastName = Column(Unicode(100), nullable=False, index=True)
    Email = Column(Unicode(100), nullable=False, index=True)
    IsSuperAdmin = Column(Boolean, nullable=False, server_default=text("((0))"))
    IsActive = Column(Boolean, nullable=False, server_default=text("((1))"))
    CreatedDateTimeUTC = Column(DATETIME2, nullable=False)
    JobTitle = Column(Unicode(200), nullable=False)
    PhoneNumber = Column(Unicode(20))
    Preferences = Column(Unicode)
    PasswordHash = Column(Unicode(100))
    TempPasswordHash = Column(Unicode(100))
    TempPasswordExpirationDateTimeUTC = Column(DATETIME2)
    ModifiedDateTimeUTC = Column(DATETIME2)
    LastLoginDateTimeUTC = Column(DATETIME2)

    @declared_attr
    def CreatedUserID(cls):
        return Column(ForeignKey("Users.ID"))

    @declared_attr
    def ModifiedUserID(cls):
        return Column(ForeignKey("Users.ID"))

    @declared_attr
    def Users(cls):
        return relationship(
            "Users",
            remote_side=[cls.ID],
            foreign_keys=[cls.CreatedUserID],
            back_populates="Users_reverse",
        )

    @declared_attr
    def Users_reverse(cls):
        return relationship(
            "Users",
            remote_side=[cls.CreatedUserID],
            foreign_keys=[cls.CreatedUserID],
            back_populates="Users",
        )

    @declared_attr
    def Users_(cls):
        return relationship(
            "Users",
            remote_side=[cls.ID],
            foreign_keys=[cls.ModifiedUserID],
            back_populates="Users__reverse",
        )

    @declared_attr
    def Users__reverse(cls):
        return relationship(
            "Users",
            remote_side=[cls.ModifiedUserID],
            foreign_keys=[cls.ModifiedUserID],
            back_populates="Users_",
        )

    @declared_attr
    def Groups(cls):
        return relationship(
            "Groups", foreign_keys="[Groups.CreatedUserID]", back_populates="Users"
        )

    @declared_attr
    def Groups_(cls):
        return relationship(
            "Groups", foreign_keys="[Groups.ModifiedUserID]", back_populates="Users_"
        )

    @declared_attr
    def UserAuthTokens(cls):
        return relationship("UserAuthTokens", back_populates="Users")

    @declared_attr
    def Alerts(cls):
        return relationship(
            "Alerts", foreign_keys="[Alerts.CreatedUserID]", back_populates="Users"
        )

    @declared_attr
    def Alerts_(cls):
        return relationship(
            "Alerts", foreign_keys="[Alerts.ModifiedUserID]", back_populates="Users_"
        )

    @declared_attr
    def UserGroups(cls):
        return relationship("UserGroups", back_populates="Users")

    @declared_attr
    def AlertLogs(cls):
        return relationship("AlertLogs", back_populates="Users")

    @declared_attr
    def AlertLogsNew(cls):
        return relationship("AlertLogsNew", back_populates="Users")

    @declared_attr
    def AlertNotifications(cls):
        return relationship("AlertNotifications", back_populates="Users")

    @declared_attr
    def DeviceRequests(cls):
        return relationship(
            "DeviceRequests",
            foreign_keys="[DeviceRequests.CreatedUserID]",
            back_populates="Users",
        )

    @declared_attr
    def DeviceRequests_(cls):
        return relationship(
            "DeviceRequests",
            foreign_keys="[DeviceRequests.ModifiedUserID]",
            back_populates="Users_",
        )


class GroupsMixin:
    __tablename__ = "Groups"

    ID = Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("(newid())"))
    Name = Column(Unicode(200), nullable=False, index=True)
    Address = Column(Unicode(100), nullable=False)
    City = Column(Unicode(100), nullable=False)
    State = Column(Unicode(100), nullable=False)
    ZipCode = Column(Unicode(10), nullable=False)
    Country = Column(Unicode(100), nullable=False)
    TimeZone = Column(Unicode(50), nullable=False)
    TemperatureUnits = Column(SmallInteger, nullable=False)
    IsActive = Column(Boolean, nullable=False, index=True, server_default=text("((1))"))
    CreatedDateTimeUTC = Column(DATETIME2, nullable=False)
    ExpectReplacementDevices = Column(
        Boolean, nullable=False, server_default=text("((0))")
    )
    ExpectReplacementDevicesTimeout = Column(
        DATETIME2, nullable=True, server_default=text("(DATEADD(MONTH, 1, GETDATE()))")
    )

    @declared_attr
    def CreatedUserID(cls):
        return Column(ForeignKey("Users.ID"), nullable=False)

    APIKey = Column(Unicode(100), nullable=False)
    IsFrostTechInternal = Column(Boolean, nullable=False, server_default=text("((0))"))
    GroupID = Column(
        BigInteger, Identity(start=1, increment=1), nullable=False, unique=True
    )
    ModifiedDateTimeUTC = Column(DATETIME2)

    @declared_attr
    def ModifiedUserID(cls):
        return Column(ForeignKey("Users.ID"))

    IsMetric = Column(Boolean)

    @declared_attr
    def Users(cls):
        return relationship(
            "Users", foreign_keys=[cls.CreatedUserID], back_populates="Groups"
        )

    @declared_attr
    def Users_(cls):
        return relationship(
            "Users", foreign_keys=[cls.ModifiedUserID], back_populates="Groups_"
        )

    @declared_attr
    def Alerts(cls):
        return relationship("Alerts", back_populates="Groups")

    @declared_attr
    def Devices(cls):
        return relationship("Devices", back_populates="Groups")

    @declared_attr
    def UserGroups(cls):
        return relationship("UserGroups", back_populates="Groups")


class Alerts(Base):
    __tablename__ = "Alerts"

    ID = Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("(newid())"))
    GroupID = Column(ForeignKey("Groups.ID"), nullable=False)
    Reading1 = Column(SmallInteger, nullable=False)
    Threshold1 = Column(SmallInteger, nullable=True)
    Temperature1 = Column(Integer, nullable=True)
    IsDisabled = Column(Boolean, nullable=False)
    IsActive = Column(Boolean, nullable=False)
    CreatedDateTimeUTC = Column(DATETIME2, nullable=False)
    CreatedUserID = Column(ForeignKey("Users.ID"), nullable=False)
    Condition1And2Operator = Column(SmallInteger)
    Reading2 = Column(SmallInteger)
    Threshold2 = Column(SmallInteger)
    Temperature2 = Column(Integer)
    TimeRangeStart = Column(Time)
    TimeRangeEnd = Column(Time)
    NumberOfHoursBetweenAlerts = Column(Integer)
    NumberOfTransmissions = Column(Integer)
    ConditionsInForecastMinutes = Column(Integer)
    ModifiedDateTimeUTC = Column(DATETIME2)
    ModifiedUserID = Column(ForeignKey("Users.ID"))
    RoadConditions = Column(String(100, "SQL_Latin1_General_CP1_CI_AS"))
    MapPinColor = Column(String(20, "SQL_Latin1_General_CP1_CI_AS"))
    Name = Column(String(100, "SQL_Latin1_General_CP1_CI_AS"))
    VisionConditions = Column(String(100, "SQL_Latin1_General_CP1_CI_AS"))

    Users = relationship("Users", foreign_keys=[CreatedUserID], back_populates="Alerts")
    Groups = relationship("Groups", back_populates="Alerts")
    Users_ = relationship(
        "Users", foreign_keys=[ModifiedUserID], back_populates="Alerts_"
    )
    Devices = relationship(
        "Devices", secondary="AlertLocations", back_populates="Alerts"
    )
    AlertLogs = relationship("AlertLogs", back_populates="Alerts")
    AlertLogsNew = relationship("AlertLogsNew", back_populates="Alerts")
    AlertTriggers = relationship("AlertTriggers", back_populates="Alerts")


class UserGroupsMixin:
    __tablename__ = "UserGroups"
    __table_args__ = (
        Index("UserGroups_UC_UserID_GroupID", "UserID", "GroupID", unique=True),
    )

    ID = Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("(newid())"))
    Permission = Column(SmallInteger, nullable=False)

    @declared_attr
    def UserID(cls):
        return Column(ForeignKey("Users.ID"), nullable=False)

    @declared_attr
    def GroupID(cls):
        return Column(ForeignKey("Groups.ID"), nullable=False)

    @declared_attr
    def Groups(cls):
        return relationship("Groups", back_populates="UserGroups")

    @declared_attr
    def Users(cls):
        return relationship("Users", back_populates="UserGroups")


t_AlertLocations = Table(
    "AlertLocations",
    metadata,
    Column("AlertID", ForeignKey("Alerts.ID"), nullable=False),
    Column("DeviceID", ForeignKey("Devices.ID"), nullable=False),
)

t_AlertRecipients = Table(
    "AlertRecipients",
    metadata,
    Column("AlertID", ForeignKey("Alerts.ID"), nullable=False),
    Column("UserID", ForeignKey("Users.ID"), nullable=False),
    Column("Phone", Boolean, nullable=False),
    Column("Email", Boolean, nullable=False),
)


class AlertLogs(Base):
    __tablename__ = "AlertLogs"

    ID = Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("(newid())"))
    AlertID = Column(ForeignKey("Alerts.ID"), nullable=False)
    UserID = Column(ForeignKey("Users.ID"), nullable=False)
    SentDateTimeUTC = Column(DATETIME2, nullable=False)
    DeliveryMethod = Column(SmallInteger, nullable=False)
    Contact = Column(Unicode(100), nullable=False)
    DeviceID = Column(ForeignKey("Devices.ID"), nullable=False)
    DeliverySucceeded = Column(Boolean, nullable=False)
    AlertBody = Column(Unicode, nullable=False)
    LatestTransmissionDateTimeUTC = Column(DATETIME2)
    NextForecastDateTimeUTC = Column(DATETIME2)

    Alerts = relationship("Alerts", back_populates="AlertLogs")
    Devices = relationship("Devices", back_populates="AlertLogs")
    Users = relationship("Users", back_populates="AlertLogs")
    __table_args__ = (
        Index(
            "ix_AlertID_DeviceID_Includes",
            "AlertID",
            "DeviceID",
            unique=False,
            mssql_include=[
                "LatestTransmissionDateTimeUTC",
                "NextForecastDateTimeUTC",
                "SentDateTimeUTC",
            ],
        ),
    )


class AlertLogsNew(Base):
    __tablename__ = "AlertLogsNew"

    ID = Column(UNIQUEIDENTIFIER, primary_key=True, server_default=text("(newid())"))
    AlertID = Column(ForeignKey("Alerts.ID"), nullable=False)
    UserID = Column(ForeignKey("Users.ID"), nullable=False)
    SentDateTimeUTC = Column(DATETIME2, nullable=False)
    DeliveryMethod = Column(SmallInteger, nullable=False)
    Contact = Column(Unicode(100), nullable=False)
    DeviceID = Column(ForeignKey("Devices.ID"), nullable=False)
    DeliverySucceeded = Column(Boolean, nullable=False)
    AlertBody = Column(Unicode, nullable=False)
    LatestTransmissionDateTimeUTC = Column(DATETIME2)
    NextForecastDateTimeUTC = Column(DATETIME2)

    Alerts = relationship("Alerts", back_populates="AlertLogsNew")
    Devices = relationship("Devices", back_populates="AlertLogsNew")
    Users = relationship("Users", back_populates="AlertLogsNew")

    __table_args__ = (
        Index(
            "iDX_AlertLogsNew_DeviceID_Includes_AlertID_SentDateTimeUTC",
            "DeviceID",
            unique=False,
            mssql_include=["AlertID", "SentDateTimeUTC"],
        ),
    )


class AlertTriggers(Base):
    __tablename__ = "AlertTriggers"

    ID = Column(BigInteger, Identity(start=1, increment=1), primary_key=True)
    AlertID = Column(ForeignKey("Alerts.ID"), nullable=False)
    DeviceID = Column(ForeignKey("Devices.ID"), nullable=False)
    DateTimeUTC = Column(DATETIME2, nullable=False)
    TriggerData = Column(JSON(True), nullable=True)

    Alerts = relationship("Alerts", back_populates="AlertTriggers")
    Devices = relationship("Devices", back_populates="AlertTriggers")
    AlertNotifications = relationship(
        "AlertNotifications", back_populates="AlertTriggers"
    )

    __table_args__ = (
        Index(
            "iDX_AlertTriggers_DeviceID_Includes_AlertID_DateTimeUTC",
            "DeviceID",
            unique=False,
            mssql_include=["AlertID", "DateTimeUTC"],
        ),
    )


class AlertNotifications(Base):
    __tablename__ = "AlertNotifications"

    ID = Column(BigInteger, Identity(start=1, increment=1), primary_key=True)
    AlertTriggerID = Column(ForeignKey("AlertTriggers.ID"), nullable=False)
    UserID = Column(ForeignKey("Users.ID"), nullable=False)
    DidSucceed = Column(Boolean, nullable=False)
    DateTimeUTC = Column(DATETIME2, nullable=False)
    AlertBody = Column(Unicode, nullable=True)
    OtherInformation = Column(Unicode, nullable=True)

    AlertTriggers = relationship("AlertTriggers", back_populates="AlertNotifications")
    Users = relationship("Users", back_populates="AlertNotifications")


class DeviceState(Base):
    __tablename__ = "DeviceStateType"
    ID = Column(SmallInteger, Identity(start=0, increment=1), primary_key=True)
    DeviceStateName = Column(String(12), nullable=False, unique=True)
    Description = Column(String(2000), nullable=False)
    CreatedDateTimeUTC = Column(DATETIME2, default=func.now())


class DeviceLineage(Base):
    __tablename__ = "DeviceLineage"

    ID = Column(BigInteger, Identity(start=0, increment=1))
    NewGroupID = Column(
        ForeignKey("Groups.GroupID"),
        nullable=False,
        default=lambda context: context.get_current_parameters()["GroupID"],
    )
    OldGroupID = Column(
        ForeignKey("Groups.GroupID"),
        nullable=False,
        default=lambda context: context.get_current_parameters()["GroupID"],
    )
    DeviceId = Column(ForeignKey("Devices.ID"), nullable=False)
    OldDeviceState = Column(
        ForeignKey(
            "DeviceStateType.ID",
        ),
        nullable=True,
    )
    NewDeviceState = Column(
        ForeignKey(
            "DeviceStateType.ID",
        ),
        nullable=False,
    )
    OldVendorDeviceID = Column(
        String(50, "SQL_Latin1_General_CP1_CI_AS"),
        nullable=False,
        index=True,
        default=lambda context: context.get_current_parameters()["VendorDeviceID"],
    )
    NewVendorDeviceID = Column(
        String(50, "SQL_Latin1_General_CP1_CI_AS"),
        nullable=False,
        index=True,
        default=lambda context: context.get_current_parameters()["VendorDeviceID"],
    )
    CreatedDateTimeUTC = Column(DATETIME2, default=func.now())
    PrimaryKeyConstraint(ID, mssql_clustered=False)
    Index(
        "IDX_CreatedDateTimeUTC",
        CreatedDateTimeUTC.desc(),
        mssql_clustered=True,
    )


class DeviceType(Base):
    __tablename__ = "DeviceType"

    ID = Column(SmallInteger, Identity(start=1, increment=1), primary_key=True)
    Name = Column(
        String(50, "SQL_Latin1_General_CP1_CI_AS"), nullable=False, unique=True
    )
    IsActive = Column(Boolean, nullable=False, server_default=text("((1))"))
    UniqueConstraint("Name", name="uq_DeviceTypeName")


class Devices(Base):
    __tablename__ = "Devices"
    __table_args__ = DEVICES_TABLE_CONSTRAINTS + ({"implicit_returning": False},)

    ID = Column(BigInteger, Identity(start=1, increment=1), primary_key=True)
    GroupID = Column(ForeignKey("Groups.GroupID"), nullable=False, index=True)
    DeviceKey = Column(
        UNIQUEIDENTIFIER, nullable=False, server_default=text("(newid())")
    )
    DeviceState = Column(
        ForeignKey(
            "DeviceStateType.ID",
        ),
        index=True,
        nullable=False,
    )
    DeviceType = Column(
        ForeignKey("DeviceType.ID"),
        nullable=False,
        index=True,
        server_default=text("(SELECT ID FROM DeviceType WHERE Name = 'Mini RWIS')"),
    )
    Revision = Column(ForeignKey("FrostDeviceRevisions.ID"), nullable=True)
    IsActive = Column(Boolean, nullable=False, index=True)
    CreatedDateTimeUTC = Column(
        DateTime, nullable=False, server_default=text("(getdate())")
    )
    CreatedUserID = Column(ForeignKey("Users.ID"), nullable=False)
    VendorDeviceID = Column(String(50, "SQL_Latin1_General_CP1_CI_AS"), index=True)
    VendorTypeCode = Column(
        String(10, "SQL_Latin1_General_CP1_CI_AS"), server_default=text("('PARTICLE')")
    )
    VendorSerialNumber = Column(String(50, "SQL_Latin1_General_CP1_CI_AS"))
    Name = Column(
        String(50, "SQL_Latin1_General_CP1_CI_AS"), index=True, nullable=False
    )
    Description = Column(String(100, "SQL_Latin1_General_CP1_CI_AS"))
    Notes = Column(String(5000, "SQL_Latin1_General_CP1_CI_AS"))
    Zone = Column(String(150, "SQL_Latin1_General_CP1_CI_AS"))
    LocationTypeID = Column(ForeignKey("LocationType.ID"))
    SurfaceTypeID = Column(ForeignKey("SurfaceType.ID"))
    TransmissionInterval = Column(Integer)
    Latitude = Column(DECIMAL(10, 6))
    Longitude = Column(DECIMAL(10, 6))
    Altitude = Column(DECIMAL(10, 6))
    Height = Column(DECIMAL(10, 2))
    SensorHeight = Column(DECIMAL(10, 2))
    Distance = Column(DECIMAL(10, 2))
    ModifiedDateTimeUTC = Column(DateTime)
    ModifiedUserID = Column(ForeignKey("Users.ID"))
    VendorProductID = Column(
        String(50, "SQL_Latin1_General_CP1_CI_AS"), server_default=text("((17735))")
    )
    LastPhotoRequestUTC = Column(DateTime)
    Alerts = relationship(
        "Alerts", secondary="AlertLocations", back_populates="Devices"
    )
    Groups = relationship("Groups", back_populates="Devices")
    LocationType = relationship("LocationType", back_populates="Devices")
    SurfaceType = relationship("SurfaceType", back_populates="Devices")
    AlertLogs = relationship("AlertLogs", back_populates="Devices")
    AlertLogsNew = relationship("AlertLogsNew", back_populates="Devices")
    AlertTriggers = relationship("AlertTriggers", back_populates="Devices")
    DeviceImages = relationship("DeviceImages", back_populates="Devices")
    DeviceReadings = relationship("DeviceReadings", back_populates="Devices")
    DeviceRequests = relationship("DeviceRequests", back_populates="Devices")


class DeviceSummary(Base):
    __tablename__ = "DeviceSummary"
    __table_args__ = (Index("IDX_DeviceSummary_DeviceID", "DeviceID", "IsActive"),)

    ID = Column(BigInteger, Identity(start=1, increment=1), nullable=False)
    DeviceID = Column(BigInteger, primary_key=True, nullable=False)
    GroupID = Column(BigInteger, primary_key=True, nullable=False)
    IsActive = Column(Boolean, nullable=False)
    CreateDateTimeUTC = Column(DateTime, nullable=False)
    DeviceImageID = Column(BigInteger)
    DeviceReadingID = Column(BigInteger)
    ModifiedDateTimeUTC = Column(DateTime)


class DeviceImages(Base):
    __tablename__ = "DeviceImages"
    __table_args__ = (
        ForeignKeyConstraint(
            ["DeviceID", "VendorImageID", "CaptureDateTimeUTC"],
            [
                "DeviceImages.DeviceID",
                "DeviceImages.VendorImageID",
                "DeviceImages.CaptureDateTimeUTC",
            ],
        ),
        Index(
            "IDX_DeviceImages_CaptureDateTimeUTC",
            "DeviceID",
            "IsComplete",
            "CaptureDateTimeUTC",
        ),
        Index(
            "IDX_DeviceImages_DeviceID_IsComplete_DeviceReadingID",
            "DeviceID",
            "IsComplete",
            "DeviceReadingID",
        ),
        Index(
            "IDX_ImageUrl",
            "ImageUrl",
        ),
        Index(
            "ix_IsCompleteCaptureDateTimeUTC_Includes",
            "IsComplete",
            "CaptureDateTimeUTC",
            mssql_include=["ID"],
        ),
    )

    ID = Column(BigInteger, Identity(start=1, increment=1), nullable=False, unique=True)
    DeviceID = Column(ForeignKey("Devices.ID"), primary_key=True, nullable=False)
    VendorImageID = Column(
        String(50, "SQL_Latin1_General_CP1_CI_AS"), primary_key=True, nullable=False
    )
    IsComplete = Column(Boolean, nullable=False, server_default=text("((0))"))
    CaptureDateTimeUTC = Column(DateTime, primary_key=True, nullable=False)
    CreateDateTimeUTC = Column(
        DateTime, nullable=False, server_default=text("(getdate())")
    )
    Size = Column(Integer)
    AmbientLight = Column(String(5, "SQL_Latin1_General_CP1_CI_AS"))
    Contrast = Column(String(5, "SQL_Latin1_General_CP1_CI_AS"))
    Brightness = Column(String(5, "SQL_Latin1_General_CP1_CI_AS"))
    Exposure = Column(String(5, "SQL_Latin1_General_CP1_CI_AS"))
    Resolution = Column(Integer)
    ImageUrl = Column(String(5000, "SQL_Latin1_General_CP1_CI_AS"))
    ModifiedDateTimeUTC = Column(DateTime)
    DeviceReadingID = Column(BigInteger)
    Devices = relationship("Devices", back_populates="DeviceImages")
    IsBurstImage = Column(Boolean, nullable=False, server_default=text("((0))"))


class DeviceReadings(Base):
    __tablename__ = "DeviceReadings"
    __table_args__ = (
        Index(
            "IDX_DeviceReadings_CaptureDateTimeUTC", "DeviceID", "CaptureDateTimeUTC"
        ),
    )

    ID = Column(BigInteger, Identity(start=1, increment=1), nullable=False, unique=True)
    DeviceID = Column(ForeignKey("Devices.ID"), primary_key=True, nullable=False)
    VendorReadingID = Column(
        String(50, "SQL_Latin1_General_CP1_CI_AS"), primary_key=True, nullable=False
    )
    CaptureDateTimeUTC = Column(DateTime, primary_key=True, nullable=False)
    CreatedDateTimeUTC = Column(
        DateTime, nullable=False, server_default=text("(getdate())")
    )
    SurfaceTemp = Column(DECIMAL(8, 2))
    AirTemp = Column(DECIMAL(6, 2))
    DewPoint = Column(DECIMAL(6, 2))
    Humidity = Column(DECIMAL(6, 2))
    HeaterTemp = Column(DECIMAL(6, 2))
    AmbientLight = Column(Integer)

    Devices = relationship("Devices", back_populates="DeviceReadings")
    Index(
        "IDX_CaptureDateTimeUTC",
        CaptureDateTimeUTC.desc(),
        mssql_clustered=True,
    )


class DeviceRequests(Base):
    __tablename__ = "DeviceRequests"
    __table_args__ = (
        Index(
            "IDX_DeviceRequests_StartDateTime_EndDateTime",
            "StartDateTimeUTC",
            "EndDateTimeUTC",
        ),
        Index(
            "IDX_DeviceRequests_DeviceID_RequestTypeCode", "DeviceID", "RequestTypeCode"
        ),
    )

    ID = Column(BigInteger, Identity(start=1, increment=1), primary_key=True)
    DeviceID = Column(ForeignKey("Devices.ID"), nullable=False)
    RequestTypeCode = Column(ForeignKey("RequestType.RequestTypeCode"), nullable=False)
    CreateDateTimeUTC = Column(
        DateTime, nullable=False, server_default=text("(getdate())")
    )
    CreatedUserID = Column(ForeignKey("Users.ID"), nullable=False)
    RequestData = Column(String(collation="SQL_Latin1_General_CP1_CI_AS"))
    ResultCode = Column(String(50, "SQL_Latin1_General_CP1_CI_AS"))
    ResultData = Column(String(collation="SQL_Latin1_General_CP1_CI_AS"))
    ReferenceNr = Column(String(50, "SQL_Latin1_General_CP1_CI_AS"))
    StartDateTimeUTC = Column(DateTime)
    EndDateTimeUTC = Column(DateTime)
    ModifiedDateTimeUTC = Column(DateTime)
    ModifiedUserID = Column(ForeignKey("Users.ID"))

    Users = relationship(
        "Users", foreign_keys=[CreatedUserID], back_populates="DeviceRequests"
    )
    Devices = relationship("Devices", back_populates="DeviceRequests")
    Users_ = relationship(
        "Users", foreign_keys=[ModifiedUserID], back_populates="DeviceRequests_"
    )
    RequestType = relationship("RequestType", back_populates="DeviceRequests")


class DeviceImageDetails(DeviceImages):
    __tablename__ = "DeviceImageDetails"
    __table_args__ = (
        Index("IX_DeviceImageDetails_DeviceImageID", "DeviceImageID", unique=False),
    )

    ID = column_property(
        Column(
            "ID",
            BigInteger,
            Identity(start=1, increment=1),
            nullable=False,
        ),
        DeviceImages.ID,
    )
    DeviceImageID = Column(
        ForeignKey("DeviceImages.ID", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    RoadConditions = Column(String(100, "SQL_Latin1_General_CP1_CI_AS"))
    WeatherConditions = Column(String(100, "SQL_Latin1_General_CP1_CI_AS"))
    CreatedDateTimeUTC = Column(DateTime)
    CreatedUserID = Column(UNIQUEIDENTIFIER)
    ModifiedDateTimeUTC = column_property(
        Column(DateTime, name="ModifiedDateTimeUTC"), DeviceImages.ModifiedDateTimeUTC
    )
    ModifiedUserID = Column(UNIQUEIDENTIFIER)


t_DeviceRequestImages = Table(
    "DeviceRequestImages",
    metadata,
    Column("ID", BigInteger, Identity(start=1, increment=1), nullable=False),
    Column("DeviceRequestID", ForeignKey("DeviceRequests.ID"), nullable=False),
    Column("DeviceImageID", BigInteger, nullable=False),
    Column("DeviceID", ForeignKey("Devices.ID")),
    Column("CaptureDateTimeUTC", DateTime),
    Index("IDX_DeviceRequestImages_DeviceRequestID", "DeviceRequestID"),
)


class Users(Base, UsersMixin): ...


class Groups(Base, GroupsMixin): ...


class UserGroups(Base, UserGroupsMixin): ...


class ComputerVision(Base):
    __tablename__ = "ComputerVision"
    ID = Column("ID", BigInteger, Identity(start=1, increment=1), nullable=False)
    ImageID = Column(
        "ImageID",
        ForeignKey("DeviceImages.ID"),
        nullable=False,
        index=True,
        primary_key=True,
    )

    NightClearPavement = Column(
        "NightClearPavement", REAL, nullable=True, server_default=text("((0))")
    )
    NightSnowing = Column(
        "NightSnowing", REAL, nullable=True, server_default=text("((0))")
    )
    NightWetPavement = Column(
        "NightWetPavement", REAL, nullable=True, server_default=text("((0))")
    )
    NightSnowOnRoad = Column(
        "NightSnowOnRoad", REAL, nullable=True, server_default=text("((0))")
    )
    NightPartialSnowOnRoad = Column(
        "NightPartialSnowOnRoad", REAL, nullable=True, server_default=text("((0))")
    )
    DaySnowing = Column("DaySnowing", REAL, nullable=True, server_default=text("((0))"))
    DayPartialSnowOnRoad = Column(
        "DayPartialSnowOnRoad", REAL, nullable=True, server_default=text("((0))")
    )
    DayClearPavement = Column(
        "DayClearPavement", REAL, nullable=True, server_default=text("((0))")
    )
    DayWetPavement = Column(
        "DayWetPavement", REAL, nullable=True, server_default=text("((0))")
    )
    DaySnowOnRoad = Column(
        "DaySnowOnRoad", REAL, nullable=True, server_default=text("((0))")
    )
    Night = Column(REAL, nullable=True, server_default=text("((0))"))
    Sunny = Column(REAL, nullable=True, server_default=text("((0))"))
    Cloudy = Column(REAL, nullable=True, server_default=text("((0))"))
    ClearPavement = Column(REAL, nullable=True, server_default=text("((0))"))
    WetPavement = Column(REAL, nullable=True, server_default=text("((0))"))
    SnowOnRoad = Column(REAL, nullable=True, server_default=text("((0))"))
    PartialSnowOnRoad = Column(REAL, nullable=True, server_default=text("((0))"))
    Snowing = Column(REAL, nullable=True, server_default=text("((0))"))
    Raining = Column(REAL, nullable=True, server_default=text("((0))"))
    IcedLens = Column(REAL, nullable=True, server_default=text("((0))"))
    ModelVersion = Column(
        String(50, "SQL_Latin1_General_CP1_CI_AS"),
        nullable=True,
        server_default=text("('NCAR Vision')"),
    )


class UserAuthTokens(Base):
    __tablename__ = "UserAuthTokens"

    UserID = Column(ForeignKey("Users.ID"), primary_key=True, nullable=False)
    AuthToken = Column(Unicode(100), primary_key=True, nullable=False)
    ExpirationDateTimeUTC = Column(
        DATETIME2, nullable=False, server_default=text("(dateadd(day,(14),getdate()))")
    )

    Users = relationship("Users", back_populates="UserAuthTokens")


class FrostDeviceRevisions(Base):
    __tablename__ = "FrostDeviceRevisions"

    ID = Column(SmallInteger, Identity(start=1, increment=1), primary_key=True)
    Name = Column(
        String(50, "SQL_Latin1_General_CP1_CI_AS"), nullable=True, unique=True
    )
    SensorHardwareID = Column(ForeignKey("SensorHardware.ID"), nullable=True)
    BluetoothHardwareID = Column(ForeignKey("BluetoothHardware.ID"), nullable=True)
    ModifiedDateTimeUTC = Column(
        DateTime, nullable=False, server_default=text("(getdate())")
    )
    IsActive = Column(Boolean, nullable=False, server_default=text("((1))"))
    Description = Column(String(2000, "SQL_Latin1_General_CP1_CI_AS"), nullable=True)
    UniqueConstraint("Name", name="uq_FrostDeviceRevisions_Name")


class SensorHardware(Base):
    __tablename__ = "SensorHardware"
    ID = Column(SmallInteger, Identity(start=1, increment=1), primary_key=True)
    VendorID = Column(String(50, "SQL_Latin1_General_CP1_CI_AS"), unique=True)
    CreatedDateTimeUTC = Column(
        DateTime, nullable=False, server_default=text("(getdate())")
    )
    UniqueConstraint("VendorID", name="uq_SensorHardware_VendorID")


class BluetoothHardware(Base):
    __tablename__ = "BluetoothHardware"
    ID = Column(BigInteger, Identity(start=1, increment=1), primary_key=True)
    VendorID = Column(String(50, "SQL_Latin1_General_CP1_CI_AS"), unique=True)
    CreatedDateTimeUTC = Column(
        DateTime, nullable=False, server_default=text("(getdate())")
    )
    UniqueConstraint("VendorID", name="uq_BluetoothHardware_VendorID")


class BluetoothEncryptionKeys(Base):
    __tablename__ = "BluetoothEncryptionKeys"
    ID = Column(BigInteger, Identity(start=1, increment=1), primary_key=True)
    DeviceID = Column(ForeignKey("Devices.ID"), nullable=False, unique=True)
    Key = Column(String(5000, "SQL_Latin1_General_CP1_CI_AS"), nullable=True)
    CreatedDateTimeUTC = Column(
        DateTime, nullable=False, server_default=text("(getdate())")
    )


class FirmwareVersions(Base):
    __tablename__ = "FirmwareVersions"
    ID = Column(SmallInteger, Identity(start=1, increment=1), primary_key=True)
    Version = Column(String(50, "SQL_Latin1_General_CP1_CI_AS"), nullable=True)
    IsActive = Column(Boolean, nullable=False, server_default=text("((1))"))
    S3ArtifactURL = Column(String(2000, "SQL_Latin1_General_CP1_CI_AS"), nullable=True)
    BinarySHA1 = Column(String(50, "SQL_Latin1_General_CP1_CI_AS"), nullable=True)


class SnowDepthReadings(Base):
    __tablename__ = "SnowDepthReadings"

    ID = Column(
        BigInteger,
        Identity(start=1, increment=1),
        nullable=False,
    )
    PrimaryKeyConstraint(ID, mssql_clustered=False)
    DeviceID = Column(ForeignKey("Devices.ID"), nullable=False)
    DistanceMm = Column(SmallInteger, nullable=False)
    BatteryMv = Column(Integer, nullable=True)
    RssiPower = Column(SmallInteger, nullable=True)
    Version = Column(Integer, nullable=True)
    TemperatureC = Column(SmallInteger, nullable=True)
    ReferenceDepthMm = Column(SmallInteger, nullable=False)
    Reserved1 = Column(SmallInteger, nullable=True)
    Reserved2 = Column(SmallInteger, nullable=True)
    Error = Column(TINYINT)
    CreatedDateTimeUTC = Column(
        DateTime, nullable=False, server_default=text("(getdate())")
    )
    CaptureDateTimeUTC = Column(DateTime, nullable=False)
    UploadedByRWIS = Column(ForeignKey("Devices.ID"), nullable=True)
    __table_args__ = (
        Index(
            "IDX_SnowDepthReadings_DeviceID_CaptureDateTimeUTC",
            DeviceID,
            CaptureDateTimeUTC.desc(),
            mssql_clustered=True,
        ),
        Index(
            "ix_UploadedBy_Includes_CaptureDateTimeUTC",
            UploadedByRWIS,
            CaptureDateTimeUTC.desc(),
            mssql_include=["DeviceID"],
        ),
    )


class SnowDepthRWISPairs(Base):
    __tablename__ = "SnowDepthRWISPairs"

    ID = Column(
        BigInteger,
        Identity(start=1, increment=1),
        nullable=False,
        unique=True,
        primary_key=True,
    )
    RWISDeviceID = Column(ForeignKey("Devices.ID"), nullable=False)
    SnowDepthDeviceID = Column(ForeignKey("Devices.ID"), nullable=False)
    CreatedDateTimeUTC = Column(
        DateTime, nullable=False, server_default=text("(getdate())")
    )
    ModifiedDateTimeUTC = Column(
        DateTime, nullable=False, server_default=text("(getdate())")
    )
    __table_args__ = (
        Index(
            "IDX_SnowDepthRWISPairs_RWISDeviceID_SnowDepthDeviceID",
            RWISDeviceID,
            SnowDepthDeviceID,
            unique=True,
        ),
    )


class SnowDepthCalibrationRequests(Base):
    __tablename__ = "SnowDepthCalibrationRequests"

    ID = Column(BigInteger, Identity(start=1, increment=1), primary_key=True)
    RWISDeviceID = Column(ForeignKey("Devices.ID"), nullable=False)
    SnowDepthDeviceID = Column(ForeignKey("Devices.ID"), nullable=False)
    RequestDateTimeUTC = Column(DateTime, nullable=False)
    CalibrationDateTimeUTC = Column(DateTime, nullable=True)
    CalibrationFailed = Column(Boolean, nullable=False, server_default=text("((0))"))


class GroupSubscriptions(Base):
    __tablename__ = "GroupSubscriptions"

    GroupID = Column(ForeignKey("Groups.GroupID"), primary_key=True, nullable=False)
    Name = Column(
        String(100, "SQL_Latin1_General_CP1_CI_AS"), primary_key=True, nullable=False
    )
    CreatedDateTimeUTC = Column(
        DateTime, nullable=False, server_default=text("(getdate())")
    )
    ModifiedDateTimeUTC = Column(
        DateTime, nullable=False, server_default=text("(getdate())")
    )


class RequestTypeNotificationTypeMap(Base):
    __tablename__ = "RequestTypeNotificationTypeMap"
    ID = Column(
        BigInteger, Identity(start=1, increment=1), primary_key=True, nullable=False
    )
    RequestTypeCode = Column(ForeignKey("RequestType.RequestTypeCode"), nullable=False)
    NotificationTypeName = Column(ForeignKey("NotificationType.Name"), nullable=False)


# Storm Definition Tables
class StormType(Base):
    __tablename__ = "StormType"

    ID = Column(SmallInteger, primary_key=True)
    Name = Column(String(50, "SQL_Latin1_General_CP1_CI_AS"), nullable=False)
    Description = Column(String(200, "SQL_Latin1_General_CP1_CI_AS"), nullable=True)
    IsActive = Column(Boolean, nullable=False, server_default=text("((1))"))


class StormStatus(Base):
    __tablename__ = "StormStatus"

    ID = Column(SmallInteger, primary_key=True)
    Name = Column(String(50, "SQL_Latin1_General_CP1_CI_AS"), nullable=False)
    Description = Column(String(200, "SQL_Latin1_General_CP1_CI_AS"), nullable=True)
    IsActive = Column(Boolean, nullable=False, server_default=text("((1))"))


class StormDefinitionType(Base):
    __tablename__ = "StormDefinitionType"

    ID = Column(SmallInteger, primary_key=True)
    Name = Column(String(50, "SQL_Latin1_General_CP1_CI_AS"), nullable=False)
    Description = Column(String(200, "SQL_Latin1_General_CP1_CI_AS"), nullable=True)
    IsActive = Column(Boolean, nullable=False, server_default=text("((1))"))


class StormThresholds(Base):
    __tablename__ = "StormThresholds"

    ID = Column(Integer, Identity(start=1, increment=1), primary_key=True)
    DeviceID = Column(ForeignKey("Devices.ID"), nullable=True)  # NULL = Frost defaults
    StormTypeID = Column(ForeignKey("StormType.ID"), nullable=False)
    StartRules = Column(JSON(True), nullable=True)
    EndRules = Column(JSON(True), nullable=True)
    IsActive = Column(Boolean, nullable=False, server_default=text("((1))"))
    CreatedDateTimeUTC = Column(
        DATETIME2(3), nullable=False, server_default=text("(getutcdate())")
    )
    CreatedUserID = Column(ForeignKey("Users.ID"), nullable=True)
    ModifiedDateTimeUTC = Column(DATETIME2(3), nullable=True)
    ModifiedUserID = Column(ForeignKey("Users.ID"), nullable=True)

    # Relationships
    Device = relationship("Devices")
    StormType = relationship("StormType")
    CreatedUser = relationship("Users", foreign_keys=[CreatedUserID])
    ModifiedUser = relationship("Users", foreign_keys=[ModifiedUserID])

    __table_args__ = (
        Index("IDX_StormThresholds_DeviceID_StormTypeID", "DeviceID", "StormTypeID"),
        UniqueConstraint(
            "DeviceID", "StormTypeID", name="UQ_StormThresholds_DeviceID_StormTypeID"
        ),
    )


class StormEvents(Base):
    __tablename__ = "StormEvents"

    ID = Column(BigInteger, Identity(start=1, increment=1), primary_key=True)

    # Device-level storm relationship (1-to-1)
    DeviceID = Column(ForeignKey("Devices.ID"), nullable=False)

    # Storm classification
    StormTypeID = Column(ForeignKey("StormType.ID"), nullable=False)
    StormStatusID = Column(ForeignKey("StormStatus.ID"), nullable=False)
    DefinitionTypeID = Column(ForeignKey("StormDefinitionType.ID"), nullable=False)

    # Trigger information
    TriggerSource = Column(String(50, "SQL_Latin1_General_CP1_CI_AS"), nullable=True)
    TriggerMetadata = Column(
        String(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=True
    )

    # Threshold snapshots for audit trail
    StartThresholdSnapshot = Column(JSON(True), nullable=True)
    EndThresholdSnapshot = Column(JSON(True), nullable=True)

    # Temporal boundaries
    StartDateTimeUTC = Column(DATETIME2(3), nullable=False)
    EndDateTimeUTC = Column(DATETIME2(3), nullable=True)

    # Metadata
    Notes = Column(String(collation="SQL_Latin1_General_CP1_CI_AS"), nullable=True)
    IsActive = Column(Boolean, nullable=False, server_default=text("((1))"))
    CreatedDateTimeUTC = Column(
        DATETIME2(3), nullable=False, server_default=text("(getutcdate())")
    )
    CreatedUserID = Column(ForeignKey("Users.ID"), nullable=True)
    ModifiedDateTimeUTC = Column(DATETIME2(3), nullable=True)
    ModifiedUserID = Column(ForeignKey("Users.ID"), nullable=True)

    # Relationships
    Device = relationship("Devices")
    StormType = relationship("StormType")
    StormStatus = relationship("StormStatus")
    DefinitionType = relationship("StormDefinitionType")
    CreatedUser = relationship("Users", foreign_keys=[CreatedUserID])
    ModifiedUser = relationship("Users", foreign_keys=[ModifiedUserID])

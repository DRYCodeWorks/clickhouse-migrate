"""
Stored Procedures Module

This module defines stored procedures for database migrations with support for:
- Version suffixes for easier feature flagging
- Configurable user permissions for SQL Server security

Usage Examples:

# Version 2 with different permissions
usp_CustomProcedure_v2 = Procedure(
    "usp_CustomProcedure",
    read_sql_file("usp_CustomProcedure_v2"),
    version=2,
    grant_users=["frost_api", "storm_service"]  # Removed admin_portal
)

The versioned approach creates procedures named:
- usp_CustomProcedure_v2

This eliminates the need for "ROLLBACK" versions and makes feature flagging easier.
"""

from helpers.abc import ABCFunction
from helpers.utils import read_sql_file

usp_api_UpsertForecastDataV2 = read_sql_file("usp_api_UpsertForecastData")


class Procedure(ABCFunction):
    def __init__(self, name, create_sqltext, version=None, grant_users=None):
        super().__init__(name, create_sqltext, version, grant_users)

    def drop_function(self, op):
        op.execute(
            f"""
            IF OBJECT_ID('[dbo].[{self.name}]') IS NOT NULL
            DROP PROCEDURE [dbo].[{self.name}]
            """
        )

    def create_function(self, op):
        # Execute the SQL
        op.execute(self.sql)

        # Grant EXECUTE permissions for stored procedures
        if self.grant_users:
            users_list = ", ".join(self.grant_users)
            op.execute(
                f"""
                GRANT EXECUTE ON OBJECT::{self.name}
                    TO {users_list};
                """
            )


usp_UpdateDeviceImages = Procedure(
    "usp_UpdateDeviceImages",
    read_sql_file("usp_UpdateDeviceImages"),
)

usp_InsertDeviceRequestImage = (
    Procedure(
        "usp_InsertDeviceRequestImage",
        read_sql_file("usp_InsertDeviceRequestImage"),
    ),
)

usp_utl_CreateNotification = Procedure(
    "usp_utl_CreateNotification",
    read_sql_file("usp_utl_CreateNotification"),
)

usp_api_UpsertForecastData = Procedure(
    "usp_api_UpsertForecastData",
    usp_api_UpsertForecastDataV2,
)

usp_InsertSnowDepthReadingV = Procedure(
    "usp_InsertSnowDepthReading",
    read_sql_file("usp_InsertSnowDepthReading"),
)

usp_api_UpsertUserConfigurationsGroups = Procedure(
    "usp_api_UpsertUserConfigurationsGroups",
    read_sql_file("usp_api_UpsertUserConfigurationsGroups"),
)

usp_api_UpsertCompletedImage = Procedure(
    "usp_api_UpsertCompletedImage",
    read_sql_file("usp_api_UpsertCompletedImage"),
)

usp_api_UpsertCompletedImage_rollback = Procedure(
    "usp_api_UpsertCompletedImage",
    read_sql_file("usp_api_UpsertCompletedImage_DEPRECATED"),
)

usp_utl_InsertDeviceImages = Procedure(
    "usp_utl_InsertDeviceImages",
    read_sql_file("usp_utl_InsertDeviceImages"),
)

usp_utl_InsertDeviceImages_rollback = Procedure(
    "usp_utl_InsertDeviceImages",
    read_sql_file("usp_utl_InsertDeviceImages_DEPRECATED"),
)

usp_api_UpsertDeviceReading = Procedure(
    "usp_api_UpsertDeviceReading",
    read_sql_file("usp_api_UpsertDeviceReading"),
)

usp_api_UpsertDeviceReading_rollback = Procedure(
    "usp_api_UpsertDeviceReading",
    read_sql_file("usp_api_UpsertDeviceReading_DEPRECATED"),
)

usp_api_InsertDeviceRequest = Procedure(
    "usp_api_InsertDeviceRequest",
    read_sql_file("usp_api_InsertDeviceRequest"),
)

usp_api_InsertDeviceRequest_rollback = Procedure(
    "usp_api_InsertDeviceRequest",
    read_sql_file("usp_api_InsertDeviceRequest_DEPRECATED"),
)

# Storm Definition Stored Procedures with versioning (1-to-1 design)
sp_CreateStormEvent_v1 = Procedure(
    "sp_CreateStormEvent",
    read_sql_file("sp_CreateStormEvent"),
    version=1,
    grant_users=["device_portal_api"],
)

sp_UpdateStormStatus_v1 = Procedure(
    "sp_UpdateStormStatus",
    read_sql_file("sp_UpdateStormStatus"),
    version=1,
    grant_users=["device_portal_api", "frost_alerts_role"],
)

sp_CreateRetroactiveStormEvents_v1 = Procedure(
    "sp_CreateRetroactiveStormEvents",
    read_sql_file("sp_CreateRetroactiveStormEvents"),
    version=1,
    grant_users=["device_portal_api"],
)

# Storm Threshold Management Procedures
sp_CreateStormEvent_v2 = Procedure(
    "sp_CreateStormEvent",
    read_sql_file("sp_CreateStormEvent_v2"),
    version=2,
    grant_users=["device_portal_api", "frost_alerts_role"],
)

sp_UpsertDeviceThreshold_v1 = Procedure(
    "sp_UpsertDeviceThreshold",
    read_sql_file("sp_UpsertDeviceThreshold"),
    version=1,
    grant_users=["device_portal_api"],
)

sp_CompleteStormEvent_v1 = Procedure(
    "sp_CompleteStormEvent",
    read_sql_file("sp_CompleteStormEvent"),
    version=1,
    grant_users=["device_portal_api", "frost_alerts_role"],
)

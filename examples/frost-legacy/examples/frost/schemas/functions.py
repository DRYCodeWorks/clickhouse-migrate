"""
Functions Module

This module defines SQL Server functions for database migrations with support for:
- Version suffixes for easier feature flagging
- Configurable user permissions for SQL Server security
- Automatic permission detection (SELECT for table-valued, EXECUTE for scalar)

Usage Examples:

# Versioned table-valued function
fn_GetDeviceData_v2 = Function(
    "fn_GetDeviceData",
    read_sql_file("fn_GetDeviceData_v2"),
    version=2,
    grant_users=["frost_api"]
)

The versioned approach creates functions named:
- fn_GetDeviceData_v2

Permissions are automatically determined:
- Table-valued functions (TF, IF, FT) get SELECT permissions
- Scalar functions get EXECUTE permissions
"""

from helpers.abc import ABCFunction
from helpers.utils import read_sql_file


class Function(ABCFunction):
    def __init__(self, name, create_sqltext, version=None, grant_users=None):
        super().__init__(name, create_sqltext, version, grant_users)

    def drop_function(self, op):
        op.execute(
            f"""
            IF OBJECT_ID('[dbo].[{self.name}]') IS NOT NULL
            DROP FUNCTION [dbo].[{self.name}]
            """
        )


fn_GetLatestDeviceReadingID = Function(
    "fn_GetLatestDeviceReadingID",
    read_sql_file("fn_GetLatestDeviceReadingID"),
)

GetProofOfWork = Function(
    "GetProofOfWork",
    read_sql_file("fn_GetProofOfWork"),
)
fn_GetDeviceRequestID = Function(
    "fn_GetDeviceRequestID",
    read_sql_file("fn_GetDeviceRequestID"),
)

fn_GetDeviceRequestID_DEPRECATED = Function(
    "fn_GetDeviceRequestID", read_sql_file("fn_GetDeviceRequestID_DEPRECATED")
)

GET_DEVICE_TYPE_NAME = Function(
    "get_device_type_name",
    read_sql_file("fn_get_device_type_name"),
)

# Storm Definition Functions with versioning
fn_GenerateStormName_v1 = Function(
    "fn_GenerateStormName",
    read_sql_file("fn_GenerateStormName"),
    version=1,
    grant_users=["device_portal_api"],
)

fn_GetStormThresholds_v1 = Function(
    "fn_GetStormThresholds",
    read_sql_file("fn_GetStormThresholds"),
    version=1,
    grant_users=["device_portal_api", "frost_alerts_role"],
)

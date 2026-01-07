USE [frost-db-prd];
CREATE ROLE [frost_forecasts_role];


-- Grant SELECT permissions on all tables in Devices, DeviceReadings, DeviceStateType, DeviceType, DeviceImages, ComputerVision, Groups
DECLARE @sql NVARCHAR(MAX) = '';
SELECT @sql = @sql + 'GRANT SELECT ON [' + SCHEMA_NAME(schema_id
) + '].[' + name + '] TO [frost_forecasts_role];' + CHAR(13)
FROM sys.tables
WHERE name IN ('Devices', 'DeviceReadings', 'DeviceStateType', 'DeviceType', 'DeviceImages', 'ComputerVision', 'Groups');
EXEC sp_executesql @sql;

GRANT SELECT ON DeviceType TO [frost_forecasts_role];


CREATE LOGIN forecasts_handler_login WITH PASSWORD = ?;
CREATE USER [forecasts_handler] FOR LOGIN [forecasts_handler_login] WITH DEFAULT_SCHEMA = [dbo];
ALTER ROLE [frost_forecasts_role] ADD MEMBER [forecasts_handler];  

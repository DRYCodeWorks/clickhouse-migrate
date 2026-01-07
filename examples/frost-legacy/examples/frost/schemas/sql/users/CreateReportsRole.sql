USE [frost-db-prd];
CREATE ROLE [frost_reports_role];


-- Grant SELECT permissions on all tables in 
DECLARE @sql NVARCHAR(MAX) = '';
SELECT @sql = @sql + 'GRANT SELECT ON [' + SCHEMA_NAME(schema_id
) + '].[' + name + '] TO [frost_reports_role];' + CHAR(13)
FROM sys.tables
WHERE name IN (
    'Tasks',
    'Devices',
    'Groups',
    'SnowDepthReadings',
    'FrostDeviceRevisions',
    'DeviceRequests',
    'DeviceReadings',
    'DeviceType',
    'DeviceImages'
);
EXEC sp_executesql @sql;


CREATE LOGIN reports_handler_login WITH PASSWORD = ?;
CREATE USER [reports_handler] FOR LOGIN [reports_handler_login] WITH DEFAULT_SCHEMA = [dbo];
ALTER ROLE [frost_reports_role] ADD MEMBER [reports_handler];  

USE [frost-db-prd];
CREATE ROLE [frost_api_role];
-- Grant SELECT permissions on all tables
DECLARE @sql NVARCHAR(MAX) = '';
SELECT @sql = @sql + 'GRANT SELECT ON [' + SCHEMA_NAME(schema_id) + '].[' + name + '] TO [frost_api_role];' + CHAR(13)
FROM sys.tables;
EXEC sp_executesql @sql;

-- Grant SELECT permissions on all views
SET @sql = '';
SELECT @sql = @sql + 'GRANT SELECT ON [' + SCHEMA_NAME(schema_id) + '].[' + name + '] TO [frost_api_role];' + CHAR(13)
FROM sys.views;
EXEC sp_executesql @sql;

-- Grant EXECUTE permissions on all functions
SET @sql = '';
SELECT @sql = @sql + 'GRANT EXECUTE ON [' + SCHEMA_NAME(schema_id) + '].[' + name + '] TO [frost_api_role];' + CHAR(13)
FROM sys.objects
WHERE type IN ('FN');
EXEC sp_executesql @sql;


SET @sql = '';
SELECT @sql = @sql + 'GRANT SELECT ON [' + SCHEMA_NAME(schema_id) + '].[' + name + '] TO [frost_api_role];' + CHAR(13)
FROM sys.objects
WHERE type IN ('IF', 'TF');
EXEC sp_executesql @sql;

-- Grant INSERT permssions on all tables
SET @sql = '';
SELECT @sql = @sql + 'GRANT INSERT ON [' + SCHEMA_NAME(schema_id) + '].[' + name + '] TO [frost_api_role];' + CHAR(13)
FROM sys.tables;
EXEC sp_executesql @sql;    

SET @sql = '';
SELECT @sql = @sql + 'GRANT UPDATE ON [' + SCHEMA_NAME(schema_id) + '].[' + name + '] TO [frost_api_role];' + CHAR(13)
FROM sys.tables;
EXEC sp_executesql @sql;    

SET @sql = '';
SELECT @sql = @sql + 'GRANT DELETE ON [' + SCHEMA_NAME(schema_id) + '].[' + name + '] TO [frost_api_role];' + CHAR(13)
FROM sys.tables;
EXEC sp_executesql @sql;    

GRANT EXECUTE on usp_api_InsertDeviceRequest to [frost_api_role];
GRANT EXECUTE on usp_api_UpdateDeviceRequest to [frost_api_role];

-- Create user device_portal_api and assign it to the frost_api_role role
CREATE LOGIN device_portal_api_login WITH PASSWORD = ?;
CREATE USER [device_portal_api] FOR LOGIN [device_portal_api_login] WITH DEFAULT_SCHEMA = [dbo];
ALTER ROLE [frost_api_role] ADD MEMBER [device_portal_api];  

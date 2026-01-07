USE [frost-db-prd];
CREATE ROLE [frost_sds_role];

-- Grant EXECUTE permissions on select Stored Procedures
GRANT EXECUTE ON [dbo].[usp_InsertSnowDepthReading] TO [frost_sds_role];

-- Select on Tables
GRANT SELECT ON [dbo].[Devices] TO [frost_sds_role];
GRANT SELECT ON [dbo].[FrostDeviceRevisions] TO [frost_sds_role];
GRANT SELECT ON [dbo].[BluetoothHardware] TO [frost_sds_role];
GRANT SELECT ON [dbo].[SensorHardware] TO [frost_sds_role];
GRANT SELECT ON [dbo].[BluetoothEncryptionKeys] TO [frost_sds_role];
GRANT SELECT ON [dbo].[DeviceType] TO [frost_sds_role];
GRANT SELECT ON [dbo].[Groups] TO [frost_sds_role];
GRANT SELECT ON [dbo].[DeviceStateType] TO [frost_sds_role];
GRANT SELECT ON [dbo].[Users] TO [frost_sds_role];
GRANT SELECT ON [dbo].[SDSEncryptionKeys] TO [frost_sds_role];

-- Insert on Tables
GRANT INSERT ON [dbo].[BluetoothEncryptionKeys] TO [frost_sds_role];
GRANT INSERT ON [dbo].[Devices] TO [frost_sds_role];


-- Create user device_portal_api and assign it to the frost_sds_role role
CREATE LOGIN sds_handler_login WITH PASSWORD = ?;
CREATE USER [sds_handler] FOR LOGIN [sds_handler_login] WITH DEFAULT_SCHEMA = [dbo];
ALTER ROLE [frost_sds_role] ADD MEMBER [sds_handler];  
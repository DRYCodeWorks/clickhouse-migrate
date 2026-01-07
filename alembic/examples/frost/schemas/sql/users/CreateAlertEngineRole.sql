USE [frost-db-prd];
CREATE ROLE [frost_alerts_role];

-- Grant EXECUTE permissions on select Stored Procedures
GRANT EXECUTE ON [dbo].[usp_InsertSnowDepthReading] TO [frost_alerts_role];

-- Select on Tables
GRANT SELECT ON [dbo].[Devices] TO [frost_alerts_role];
GRANT SELECT ON [dbo].[DeviceType] TO [frost_alerts_role];
GRANT SELECT ON [dbo].[Groups] TO [frost_alerts_role];
GRANT SELECT ON [dbo].[Users] TO [frost_alerts_role];
GRANT SELECT ON [dbo].[UserGroups] TO [frost_alerts_role];
GRANT SELECT ON [dbo].[AlertLogsNew] TO [frost_alerts_role];
GRANT SELECT ON [dbo].[Alerts] TO [frost_alerts_role];
GRANT SELECT ON [dbo].[AlertLocations] TO [frost_alerts_role];
GRANT SELECT ON [dbo].[AlertRecipients] TO [frost_alerts_role];
GRANT SELECT ON [dbo].[DeviceImages] TO [frost_alerts_role];
GRANT SELECT ON [dbo].[DeviceReadings] TO [frost_alerts_role];


-- Insert on Tables
GRANT INSERT ON [dbo].[AlertLogsNew] TO [frost_alerts_role];


-- Create user device_portal_api and assign it to the frost_alerts_role role
CREATE LOGIN alerts_handler_login WITH PASSWORD = ?;
CREATE USER [alerts_handler] FOR LOGIN [alerts_handler_login] WITH DEFAULT_SCHEMA = [dbo];
ALTER ROLE [frost_alerts_role] ADD MEMBER [alerts_handler];  
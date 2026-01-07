USE [frost-db-prd];
CREATE ROLE [frost_cv_role];

-- Grant EXECUTE permissions on select Stored Procedures
GRANT EXECUTE ON [dbo].[usp_api_UpsertCompletedImage] TO [frost_cv_role];
GRANT EXECUTE ON [dbo].[usp_UpdateDeviceImages] TO [frost_cv_role];

-- Select on Devices
GRANT SELECT ON [dbo].[Devices] TO [frost_cv_role];
GRANT SELECT ON [dbo].[DeviceImages] TO [frost_cv_role];
GRANT SELECT ON [dbo].[ComputerVision] TO [frost_cv_role];

GRANT INSERT ON [dbo].[ComputerVision] TO [frost_cv_role];

-- Create user device_portal_api and assign it to the frost_cv_role role
CREATE LOGIN cv_handler_login WITH PASSWORD = ?;
CREATE USER [cv_handler] FOR LOGIN [cv_handler_login] WITH DEFAULT_SCHEMA = [dbo];
ALTER ROLE [frost_cv_role] ADD MEMBER [cv_handler];  
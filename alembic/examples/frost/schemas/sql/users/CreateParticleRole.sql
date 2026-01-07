USE [frost-db-prd];
CREATE ROLE [frost_particle_role];

-- Grant EXECUTE permissions on select Stored Procedures
GRANT EXECUTE ON [dbo].[usp_api_InsertDeviceRequest] TO [frost_particle_role];
GRANT EXECUTE ON [dbo].[usp_api_UpdateDeviceRequest] TO [frost_particle_role];
GRANT EXECUTE ON [dbo].[usp_api_UpsertCompletedImage] TO [frost_particle_role];
GRANT EXECUTE ON [dbo].[usp_api_UpsertDeviceReading] TO [frost_particle_role];
GRANT EXECUTE ON [dbo].[usp_InsertDeviceRequestImage] TO [frost_particle_role];
GRANT EXECUTE ON [dbo].[usp_UpdateDeviceImages] TO [frost_particle_role];
GRANT EXECUTE ON [dbo].[usp_utl_InsertDeviceImages] TO [frost_particle_role];

-- Select on Devices
GRANT SELECT ON [dbo].[Devices] TO [frost_particle_role];
GRANT SELECT ON [dbo].[DeviceImages] TO [frost_particle_role];
GRANT SELECT ON [dbo].[DeviceRequests] TO [frost_particle_role];

-- Insert 
GRANT INSERT ON [dbo].[DeviceRequestImages] TO [frost_particle_role];

-- Create user device_portal_api and assign it to the frost_particle_role role
CREATE LOGIN particle_handler_login WITH PASSWORD = ?;
CREATE USER [particle_handler] FOR LOGIN [particle_handler_login] WITH DEFAULT_SCHEMA = [dbo];
ALTER ROLE [frost_particle_role] ADD MEMBER [particle_handler];  
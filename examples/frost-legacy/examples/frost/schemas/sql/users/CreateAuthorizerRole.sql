USE [frost-db-prd];
CREATE ROLE [frost_api_authorizer_role];


GRANT SELECT ON [dbo].[Groups] TO [frost_api_authorizer_role];
GRANT SELECT ON [dbo].[UserGroups] TO [frost_api_authorizer_role];
GRANT SELECT ON [dbo].[UserDevices] TO [frost_api_authorizer_role];
GRANT SELECT ON [dbo].[Devices] TO [frost_api_authorizer_role];
GRANT SELECT ON [dbo].[GroupSubscriptions] TO [frost_api_authorizer_role];
GRANT SELECT ON [dbo].[UserAuthTokens] TO [frost_api_authorizer_role];
GRANT SELECT ON [dbo].[Users] TO [frost_api_authorizer_role];

-- Create user device_portal_api and assign it to the frost_api_authorizer_role role
CREATE LOGIN api_authorizer_handler_login WITH PASSWORD = ?;
CREATE USER [api_authorizer_handler] FOR LOGIN [api_authorizer_handler_login] WITH DEFAULT_SCHEMA = [dbo];
ALTER ROLE [frost_api_authorizer_role] ADD MEMBER [api_authorizer_handler];  
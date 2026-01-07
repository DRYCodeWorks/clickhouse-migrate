USE [frost-db-prd];

-- Select on Tables
GRANT SELECT ON [dbo].[AlertTriggers] TO [frost_api_role];
GRANT SELECT ON [dbo].[AlertNotifications] TO [frost_api_role];


-- Insert on Tables
GRANT INSERT ON [dbo].[AlertTriggers] TO [frost_api_role];
GRANT INSERT ON [dbo].[AlertNotifications] TO [frost_api_role];
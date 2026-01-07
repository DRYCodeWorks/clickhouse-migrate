USE [frost-db-prd];

-- Select on Tables
REVOKE SELECT ON [dbo].[AlertTriggers] TO [frost_alerts_role];
REVOKE SELECT ON [dbo].[AlertNotifications] TO [frost_alerts_role];


-- Insert on Tables
REVOKE INSERT ON [dbo].[AlertTriggers] TO [frost_alerts_role];
REVOKE INSERT ON [dbo].[AlertNotifications] TO [frost_alerts_role];
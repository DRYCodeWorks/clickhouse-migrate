SET param_db_name = 'frost_dev';
SET param_service_user_name = 'dans_service_user';
SET param_service_role_name = 'developer_admin_role';
SET param_password = '';

-- CREATE USER IF NOT EXISTS dans_service_user IDENTIFIED WITH SHA256_PASSWORD BY {password: String};

-- Create the developer admin role
CREATE ROLE IF NOT EXISTS developer_admin_role;


GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, ALTER ON frost_dev.* TO developer_admin_role;
-- Grant system table access for monitoring and debugging
GRANT CURRENT GRANTS ON system.* TO developer_admin_role;
GRANT CURRENT GRANTS ON information_schema.* TO developer_admin_role;
-- Grant ability to show databases and tables
GRANT SHOW DATABASES ON *.* TO developer_admin_role;
GRANT SHOW TABLES ON *.* TO developer_admin_role;
GRANT CREATE DATABASE ON *.* TO developer_admin_role;
-- GRANT DROP DATABASE ON *.* TO developer_admin_role;

-- Grant the role to your user
GRANT developer_admin_role TO dans_service_user;

-- Set it as the default role (so it's active on login)
SET DEFAULT ROLE developer_admin_role TO dans_service_user;
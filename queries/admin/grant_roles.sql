-- create an admin user and grant it admin credentials to clickhouse
-- Create an admin user and grant it admin credentials
CREATE USER admin IDENTIFIED WITH sha256_password BY {password};

-- Grant all privileges to the admin user
CREATE ROLE admin_role;



GRANT SELECT, INSERT, ALTER UPDATE, ALTER DELETE ON dev_db.* TO admin_role;

-- Grant table management permissions
GRANT CREATE TABLE, DROP TABLE, TRUNCATE ON dev_db.* TO admin_role;

-- Grant permissions for schema inspection
GRANT SHOW DATABASES, SHOW TABLES, SHOW COLUMNS ON dev_db.* TO admin_role;

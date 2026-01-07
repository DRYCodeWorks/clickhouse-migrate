-- Bootstrap script for ClickHouse database
-- Creates database, dict_reader user, and service user

-- Create database
CREATE DATABASE IF NOT EXISTS {db};

-- Create dict_reader user (for dictionary sources)
CREATE USER IF NOT EXISTS {dict_reader_name}
IDENTIFIED BY '{dict_reader_password}';

-- Create service user (for migrations and application)
CREATE USER IF NOT EXISTS {service_user}
IDENTIFIED BY '{service_password}';

-- Grant permissions to service user
GRANT ALL ON {db}.* TO {service_user};
GRANT CREATE TEMPORARY TABLE ON *.* TO {service_user}

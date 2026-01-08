-- Bootstrap SQL Reference
-- This file documents the SQL structure created by `ch-migrate bootstrap`
-- The actual SQL is generated dynamically by bootstrap.py
--
-- IMPORTANT: This file is NOT executed directly. It serves as documentation.
-- To run bootstrap, use: ch-migrate bootstrap <environment>

-- =============================================================================
-- DATABASE
-- =============================================================================

CREATE DATABASE IF NOT EXISTS {db};

-- =============================================================================
-- ROLES
-- =============================================================================

-- Migration role: full access for schema changes and data operations (required)
CREATE ROLE IF NOT EXISTS {project}_migration_role;
GRANT ALL ON {db}.* TO {project}_migration_role;
GRANT CREATE TEMPORARY TABLE ON *.* TO {project}_migration_role;

-- Read-only role: for MCP tools and reporting (optional, if mcp_user_name configured)
CREATE ROLE IF NOT EXISTS {project}_readonly_role;
GRANT SELECT ON {db}.* TO {project}_readonly_role;
GRANT SHOW TABLES ON {db}.* TO {project}_readonly_role;

-- Dict reader role: for dictionary sources (optional, if dict_reader_name configured)
CREATE ROLE IF NOT EXISTS {project}_dict_role;
-- SELECT grants added per-table when dictionaries are created

-- =============================================================================
-- USERS
-- =============================================================================

-- Migration user (required)
CREATE USER IF NOT EXISTS {migration_user}
IDENTIFIED BY '{migration_password}';
GRANT {project}_migration_role TO {migration_user};

-- MCP user (optional) - read-only access for AI tools
CREATE USER IF NOT EXISTS {mcp_user_name}
IDENTIFIED BY '{mcp_password}';
GRANT {project}_readonly_role TO {mcp_user_name};

-- Dict reader user (optional) - for dictionary sources
CREATE USER IF NOT EXISTS {dict_reader_name}
IDENTIFIED BY '{dict_reader_password}';
GRANT {project}_dict_role TO {dict_reader_name};

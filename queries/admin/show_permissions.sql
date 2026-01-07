-- Show permissions for a specific user
-- Usage: Set the user parameter before running
-- SET param_username = 'dan_service_user';

-- Show all grants for the user
SHOW GRANTS FOR {username: Identifier};

-- Show roles assigned to the user
SELECT *
FROM system.role_grants
WHERE user_name = {username: String};

-- Show all privileges through roles
SELECT DISTINCT
    rg.granted_role_name as role,
    g.privilege,
    g.database,
    g.table
FROM system.role_grants rg
LEFT JOIN system.grants g ON g.role_name = rg.granted_role_name
WHERE rg.user_name = {username: String}
ORDER BY role, database, table, privilege;
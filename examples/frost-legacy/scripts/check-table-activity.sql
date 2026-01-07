-- Check if target tables are currently being written to
-- Run these queries to determine if it's safe to drop the tables

-- 1. Check for active connections and sessions using these tables
SELECT DISTINCT
    s.session_id,
    s.login_name,
    s.program_name,
    s.host_name,
    s.status,
    r.command,
    r.blocking_session_id,
    t.text AS current_sql
FROM sys.dm_exec_sessions s
LEFT JOIN sys.dm_exec_requests r ON s.session_id = r.session_id
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) t
WHERE t.text LIKE '%DeviceReadings%'
   OR t.text LIKE '%DeviceImages%' 
   OR t.text LIKE '%ComputerVision%'
   OR t.text LIKE '%SnowDepthReadings%'
ORDER BY s.session_id;

-- 2. Check recent transaction log activity for these tables
SELECT 
    o.name AS table_name,
    SUM(CASE WHEN operation = 'LOP_INSERT_ROWS' THEN 1 ELSE 0 END) AS inserts,
    SUM(CASE WHEN operation = 'LOP_MODIFY_ROW' THEN 1 ELSE 0 END) AS updates,
    SUM(CASE WHEN operation = 'LOP_DELETE_ROWS' THEN 1 ELSE 0 END) AS deletes,
    COUNT(*) AS total_operations
FROM sys.fn_dblog(NULL, NULL) l
JOIN sys.objects o ON l.AllocUnitId = (
    SELECT TOP 1 allocation_unit_id 
    FROM sys.allocation_units au
    JOIN sys.partitions p ON au.container_id = p.partition_id
    WHERE p.object_id = o.object_id
)
WHERE o.name IN ('DeviceReadings', 'DeviceImages', 'ComputerVision', 'SnowDepthReadings')
  AND l.operation IN ('LOP_INSERT_ROWS', 'LOP_MODIFY_ROW', 'LOP_DELETE_ROWS')
GROUP BY o.name
ORDER BY total_operations DESC;

-- 3. Check for locks on these tables
SELECT 
    l.resource_type,
    l.resource_database_id,
    l.resource_associated_entity_id,
    o.name AS table_name,
    l.request_mode,
    l.request_type,
    l.request_status,
    s.session_id,
    s.login_name,
    s.program_name
FROM sys.dm_tran_locks l
JOIN sys.objects o ON l.resource_associated_entity_id = o.object_id
JOIN sys.dm_exec_sessions s ON l.request_session_id = s.session_id
WHERE o.name IN ('DeviceReadings', 'DeviceImages', 'ComputerVision', 'SnowDepthReadings')
  AND l.resource_type = 'OBJECT'
ORDER BY o.name, s.session_id;

-- 4. Check when these tables were last modified
SELECT 
    OBJECT_NAME(object_id) AS table_name,
    last_user_update,
    last_user_lookup,
    last_user_scan,
    user_updates,
    user_lookups,
    user_scans
FROM sys.dm_db_index_usage_stats
WHERE database_id = DB_ID()
  AND OBJECT_NAME(object_id) IN ('DeviceReadings', 'DeviceImages', 'ComputerVision', 'SnowDepthReadings')
  AND index_id = 1  -- Clustered index
ORDER BY last_user_update DESC;

-- 5. Check for running backup/maintenance operations
SELECT 
    session_id,
    command,
    status,
    percent_complete,
    estimated_completion_time,
    wait_type,
    wait_time,
    last_wait_type
FROM sys.dm_exec_requests
WHERE command LIKE '%BACKUP%' 
   OR command LIKE '%RESTORE%'
   OR command LIKE '%DBCC%'
   OR command LIKE '%INDEX%';

-- 6. Check for any foreign key dependencies that might prevent dropping
SELECT 
    fk.name AS foreign_key_name,
    OBJECT_NAME(fk.parent_object_id) AS referencing_table,
    OBJECT_NAME(fk.referenced_object_id) AS referenced_table,
    c1.name AS referencing_column,
    c2.name AS referenced_column
FROM sys.foreign_keys fk
JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
JOIN sys.columns c1 ON fkc.parent_object_id = c1.object_id AND fkc.parent_column_id = c1.column_id
JOIN sys.columns c2 ON fkc.referenced_object_id = c2.object_id AND fkc.referenced_column_id = c2.column_id
WHERE OBJECT_NAME(fk.parent_object_id) IN ('DeviceReadings', 'DeviceImages', 'ComputerVision', 'SnowDepthReadings')
   OR OBJECT_NAME(fk.referenced_object_id) IN ('DeviceReadings', 'DeviceImages', 'ComputerVision', 'SnowDepthReadings');

-- 7. Real-time monitoring query (run for 30-60 seconds to observe activity)
-- This will show ongoing operations - press Ctrl+C to stop
DECLARE @start_time DATETIME2 = GETDATE();
PRINT 'Monitoring table activity for 60 seconds...';
PRINT 'Press Ctrl+C to stop monitoring';

WHILE DATEDIFF(SECOND, @start_time, GETDATE()) < 60
BEGIN
    SELECT 
        GETDATE() AS check_time,
        DB_NAME(database_id) AS database_name,
        OBJECT_NAME(object_id) AS table_name,
        index_id,
        user_seeks,
        user_scans,
        user_lookups,
        user_updates,
        last_user_seek,
        last_user_scan,
        last_user_lookup,
        last_user_update
    FROM sys.dm_db_index_usage_stats
    WHERE database_id = DB_ID()
      AND OBJECT_NAME(object_id) IN ('DeviceReadings', 'DeviceImages', 'ComputerVision', 'SnowDepthReadings')
      AND last_user_update > DATEADD(MINUTE, -1, GETDATE())
    ORDER BY last_user_update DESC;
    
    WAITFOR DELAY '00:00:05';  -- Wait 5 seconds between checks
END

PRINT 'Monitoring completed.';
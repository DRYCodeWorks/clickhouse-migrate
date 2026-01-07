-- Show queries run by a specific user
-- Usage: Replace @UserName with the actual username you want to search for

DECLARE @UserName NVARCHAR(128) = 'admin';
DECLARE @HoursBack INT = 24; -- Look back 4 hours

-- Optimized query focusing on recent executions and currently running queries
SELECT TOP 100
    'Cached' AS query_source,
    qs.last_execution_time,
    qs.creation_time,
    qs.execution_count,
    qs.total_elapsed_time / qs.execution_count / 1000000.0 AS avg_elapsed_seconds,
    qs.total_worker_time / 1000000.0 AS total_cpu_seconds,
    qs.total_logical_reads,
    DB_NAME(qt.dbid) AS database_name,
    SUBSTRING(qt.text, (qs.statement_start_offset/2) + 1,
        ((CASE qs.statement_end_offset
            WHEN -1 THEN DATALENGTH(qt.text)
            ELSE qs.statement_end_offset
        END - qs.statement_start_offset)/2) + 1) AS query_text
FROM sys.dm_exec_query_stats qs
CROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) qt
WHERE qs.last_execution_time >= DATEADD(HOUR, -@HoursBack, GETDATE())
    AND qt.text LIKE '%' + @UserName + '%'
    AND qt.text NOT LIKE '%sys.dm_exec%' -- Exclude this monitoring query

UNION ALL

-- Currently running queries
SELECT 
    'Active' AS query_source,
    r.start_time AS last_execution_time,
    r.start_time AS creation_time,
    1 AS execution_count,
    r.total_elapsed_time / 1000.0 AS avg_elapsed_seconds,
    r.cpu_time / 1000.0 AS total_cpu_seconds,
    r.logical_reads AS total_logical_reads,
    DB_NAME(r.database_id) AS database_name,
    SUBSTRING(t.text, (r.statement_start_offset/2) + 1,
        ((CASE r.statement_end_offset
            WHEN -1 THEN DATALENGTH(t.text)
            ELSE r.statement_end_offset
        END - r.statement_start_offset)/2) + 1) AS query_text
FROM sys.dm_exec_sessions s
INNER JOIN sys.dm_exec_requests r ON s.session_id = r.session_id
CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) t
WHERE s.login_name = @UserName
    AND s.is_user_process = 1

ORDER BY last_execution_time DESC;

-- Alternative approach using Extended Events or SQL Server Audit if configured
-- This requires appropriate permissions and setup

-- Option 2: If you have Query Store enabled (SQL Server 2016+)

-- SELECT TOP 100
--     qsq.last_execution_time,
--     qsq.execution_count,
--     qsq.avg_duration / 1000000.0 AS avg_duration_seconds,
--     qsq.avg_cpu_time / 1000000.0 AS avg_cpu_seconds,
--     qsq.avg_logical_io_reads,
--     qst.query_sql_text,
--     qsp.query_plan,
--     DB_NAME() AS database_name
-- FROM sys.query_store_query_text qst
-- INNER JOIN sys.query_store_query qsq ON qst.query_text_id = qsq.query_text_id
-- INNER JOIN sys.query_store_plan qsp ON qsq.query_id = qsp.query_id
-- INNER JOIN sys.query_store_runtime_stats qrs ON qsp.plan_id = qrs.plan_id
-- WHERE qst.query_sql_text LIKE '%' + @UserName + '%'
--     OR EXISTS (
--         SELECT 1
--         FROM sys.query_context_settings qcs
--         WHERE qcs.context_settings_id = qsq.context_settings_id
--             AND qcs.set_options & 1 = 1 -- Check for specific user context if tracked
--     )
-- ORDER BY qsq.last_execution_time DESC;


-- Option 3: Check currently running queries by user

-- SELECT 
--     s.session_id,
--     s.login_name,
--     s.host_name,
--     s.program_name,
--     r.start_time,
--     r.status,
--     r.command,
--     r.wait_type,
--     r.wait_time,
--     r.cpu_time,
--     r.total_elapsed_time / 1000.0 AS elapsed_seconds,
--     t.text AS query_text,
--     SUBSTRING(t.text, (r.statement_start_offset/2) + 1,
--         ((CASE r.statement_end_offset
--             WHEN -1 THEN DATALENGTH(t.text)
--             ELSE r.statement_end_offset
--         END - r.statement_start_offset)/2) + 1) AS current_statement,
--     qp.query_plan
-- FROM sys.dm_exec_sessions s
-- INNER JOIN sys.dm_exec_requests r ON s.session_id = r.session_id
-- CROSS APPLY sys.dm_exec_sql_text(r.sql_handle) t
-- CROSS APPLY sys.dm_exec_query_plan(r.plan_handle) qp
-- WHERE s.login_name = @UserName
--     AND s.is_user_process = 1
-- ORDER BY r.start_time DESC;

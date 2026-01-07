-- Query to show SQL Server users with active sessions in the last few minutes
-- This query displays user sessions that have been active within the specified time window

DECLARE @MinutesBack INT = 5; -- Change this value to look back more/less minutes

SELECT 
    s.session_id,
    s.login_name,
    s.host_name,
    s.program_name,
    s.client_interface_name,
    s.login_time,
    s.last_request_start_time,
    s.last_request_end_time,
    DATEDIFF(MINUTE, s.last_request_end_time, GETDATE()) AS minutes_since_last_activity,
    s.status,
    s.cpu_time,
    s.memory_usage,
    s.total_elapsed_time,
    s.reads,
    s.writes,
    s.logical_reads,
    DB_NAME(s.database_id) AS database_name,
    r.command,
    r.percent_complete,
    r.wait_type,
    r.wait_time,
    r.blocking_session_id,
    t.text AS last_sql_text
FROM sys.dm_exec_sessions s
LEFT JOIN sys.dm_exec_requests r ON s.session_id = r.session_id
OUTER APPLY sys.dm_exec_sql_text(r.sql_handle) t
WHERE 
    s.is_user_process = 1  -- Only user sessions, not system processes
    AND s.session_id <> @@SPID  -- Exclude current session
    AND (
        -- Sessions with active requests
        r.session_id IS NOT NULL
        OR
        -- Sessions that were active in the last N minutes
        DATEDIFF(MINUTE, s.last_request_end_time, GETDATE()) <= @MinutesBack
    )
ORDER BY 
    CASE 
        WHEN r.session_id IS NOT NULL THEN 0  -- Active sessions first
        ELSE 1 
    END,
    s.last_request_start_time DESC;

-- Alternative query focusing on connection time and activity summary
SELECT 
    s.login_name,
    COUNT(DISTINCT s.session_id) AS active_session_count,
    MIN(s.login_time) AS earliest_login,
    MAX(s.last_request_start_time) AS most_recent_activity,
    SUM(s.cpu_time) AS total_cpu_time,
    SUM(s.memory_usage * 8) AS total_memory_kb,  -- memory_usage is in 8KB pages
    SUM(s.reads) AS total_reads,
    SUM(s.writes) AS total_writes
FROM sys.dm_exec_sessions s
LEFT JOIN sys.dm_exec_requests r ON s.session_id = r.session_id
WHERE 
    s.is_user_process = 1
    AND s.session_id <> @@SPID
    AND (
        r.session_id IS NOT NULL
        OR DATEDIFF(MINUTE, s.last_request_end_time, GETDATE()) <= @MinutesBack
    )
GROUP BY s.login_name
ORDER BY most_recent_activity DESC;
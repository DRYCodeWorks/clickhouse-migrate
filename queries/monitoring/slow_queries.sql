-- Find slow queries in the system
-- Helps identify performance bottlenecks

SELECT
    query_id,
    user,
    round(query_duration_ms / 1000, 2) AS duration_seconds,
    formatReadableSize(memory_usage) AS memory,
    formatReadableQuantity(read_rows) AS rows_read,
    formatReadableSize(read_bytes) AS bytes_read,
    substring(query, 1, 100) AS query_start,
    event_time
FROM system.query_log
WHERE type = 'QueryFinish'
    AND query_duration_ms > 1000  -- Queries longer than 1 second
    AND event_date >= today() - 7  -- Last 7 days
    AND query NOT LIKE '%system.query_log%'  -- Exclude this query
ORDER BY query_duration_ms DESC
LIMIT 20;
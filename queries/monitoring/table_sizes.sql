-- Show table sizes and row counts for current database
-- Provides insight into storage usage and table growth

SELECT
    table,
    formatReadableSize(sum(bytes)) AS size,
    formatReadableQuantity(sum(rows)) AS rows,
    max(modification_time) AS latest_modification,
    formatReadableSize(sum(bytes) / sum(rows)) AS avg_row_size,
    count() AS parts_count
FROM system.parts
WHERE active = 1
    AND database = currentDatabase()
GROUP BY table
ORDER BY sum(bytes) DESC;
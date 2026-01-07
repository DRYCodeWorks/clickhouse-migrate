-- New script in metopio-staging.
-- Date: Oct 9, 2025
-- Time: 2:46:51 PM
SET param_table_name = 'geo_indicators'

SELECT
    column,
    formatReadableSize(sum(column_data_compressed_bytes)) AS compressed_size,
    formatReadableSize(sum(column_data_uncompressed_bytes)) AS uncompressed_size,
    round(sum(column_data_uncompressed_bytes) / sum(column_data_compressed_bytes), 2) AS compression_ratio
FROM system.parts_columns
WHERE active = 1
    AND table = {table_name: String}
GROUP BY column
ORDER BY sum(column_data_compressed_bytes) DESC;
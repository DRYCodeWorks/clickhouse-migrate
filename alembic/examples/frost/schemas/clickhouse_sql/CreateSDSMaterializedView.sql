CREATE MATERIALIZED VIEW get_latest_sds_readings TO latest_sds_readings AS
SELECT *
FROM sds_readings
WHERE tuple(DeviceID, CaptureDateTimeUTC) IN (
    SELECT tuple(DeviceID, max(CaptureDateTimeUTC) AS max_capture_time) 
    FROM sds_readings
        WHERE Error = 0
        GROUP BY DeviceID
    )
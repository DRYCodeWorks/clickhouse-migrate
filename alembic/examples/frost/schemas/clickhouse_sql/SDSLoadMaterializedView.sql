INSERT INTO latest_sds_readings
SELECT *
FROM sds_readings
WHERE tuple(DeviceID, CaptureDateTimeUTC) in (
    SELECT tuple(DeviceID, max(CaptureDateTimeUTC) as max_capture_time) 
    FROM sds_readings
        WHERE Error = 0
        GROUP BY DeviceID
    )
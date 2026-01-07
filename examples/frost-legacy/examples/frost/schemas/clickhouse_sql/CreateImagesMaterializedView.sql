CREATE MATERIALIZED VIEW get_latest_images TO latest_images AS
SELECT *
FROM images
WHERE tuple(DeviceID, CaptureDateTimeUTC) in (
    SELECT tuple(DeviceID, max(CaptureDateTimeUTC) as max_capture_time) 
    FROM images
        WHERE IsComplete = 1
        GROUP BY DeviceID
    )
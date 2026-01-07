CREATE MATERIALIZED VIEW get_latest_cv_images TO latest_cv_images AS
SELECT *
FROM images
WHERE tuple(DeviceID, CaptureDateTimeUTC) in (
    SELECT tuple(DeviceID, max(CaptureDateTimeUTC) as max_capture_time) 
    FROM images
        WHERE Version = 3
        GROUP BY DeviceID
    )
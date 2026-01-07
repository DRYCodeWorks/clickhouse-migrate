INSERT INTO latest_cv_images
SELECT *
FROM images
WHERE tuple(DeviceID, CaptureDateTimeUTC) in (
    SELECT tuple(DeviceID, max(CaptureDateTimeUTC) as max_capture_time) 
    FROM images
        WHERE Version = 3
        GROUP BY DeviceID
    )
INSERT INTO latest_images SELECT *
FROM images
WHERE tuple(DeviceID, CaptureDateTimeUTC) IN (
    SELECT tuple(DeviceID, max(CaptureDateTimeUTC) AS max_capture_time) 
    FROM images
        WHERE IsComplete = 1
        GROUP BY DeviceID
    )
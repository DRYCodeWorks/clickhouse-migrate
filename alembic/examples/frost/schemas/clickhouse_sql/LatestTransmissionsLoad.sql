INSERT INTO latest_transmissions SELECT *
FROM transmissions
WHERE tuple(DeviceID, CaptureDateTimeUTC) IN (
    SELECT tuple(DeviceID, max(CaptureDateTimeUTC) AS max_capture_time) 
    FROM transmissions       
    GROUP BY DeviceID
)
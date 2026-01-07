CREATE MATERIALIZED VIEW get_latest_transmissions TO latest_transmissions AS
SELECT *
FROM transmissions
WHERE tuple(DeviceID, CaptureDateTimeUTC) in (
    SELECT tuple(DeviceID, max(CaptureDateTimeUTC) as max_capture_time) 
    FROM transmissions
    GROUP BY DeviceID
)
SELECT * FROM DeviceReadings
WHERE CaptureDateTimeUTC >= ? AND CaptureDateTimeUTC < ?
ORDER BY CaptureDateTimeUTC DESC
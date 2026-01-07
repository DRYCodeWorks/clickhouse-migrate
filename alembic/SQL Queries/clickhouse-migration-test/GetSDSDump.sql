SELECT * FROM SnowDepthReadings
WHERE CaptureDateTimeUTC >= ? AND CaptureDateTimeUTC < ?
ORDER BY CaptureDateTimeUTC DESC
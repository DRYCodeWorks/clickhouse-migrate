ALTER TABLE sds_readings 
ADD PROJECTION proj_by_uploaded_by_rwis_id (
    SELECT 
        BatteryMv, 
        CaptureDateTimeUTC, 
        CreatedDateTimeUTC, 
        DeviceID, 
        DistanceMm, 
        Error, 
        ID, 
        ReferenceDepthMm, 
        Reserved1, 
        Reserved2, 
        RssiPower, 
        TemperatureC, 
        UploadedByRWIS, 
        Version 
    ORDER BY UploadedByRWIS, CaptureDateTimeUTC
)


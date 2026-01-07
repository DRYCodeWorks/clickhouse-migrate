-- Generates a storm name based on device and timestamp
-- Used for consistent naming of device-specific storm events
CREATE FUNCTION fn_GenerateStormName_v1
(
    @DeviceID BIGINT,
    @StartDateTimeUTC DATETIME2(3)
)
RETURNS NVARCHAR(200)
AS
BEGIN
    DECLARE @DeviceName NVARCHAR(100);
    DECLARE @FormattedDate NVARCHAR(50);
    
    -- Get device name  
    SELECT @DeviceName = ISNULL(Name, CAST(@DeviceID AS NVARCHAR(20)))
    FROM Devices 
    WHERE ID = @DeviceID;
    
    -- Format date for storm name
    SET @FormattedDate = FORMAT(@StartDateTimeUTC, 'yyyy-MM-dd HH:mm');
    
    -- Build storm name: DeviceName - YYYY-MM-DD HH:MM UTC
    RETURN CONCAT(@DeviceName, ' - ', @FormattedDate, ' UTC');
END;
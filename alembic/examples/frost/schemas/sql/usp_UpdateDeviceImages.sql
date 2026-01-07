CREATE PROCEDURE
    [dbo].[usp_UpdateDeviceImages] (@DeviceImageID BIGINT, @DeviceReadingID BIGINT, @IsComplete BIT) AS BEGIN
UPDATE DeviceImages
SET
    IsComplete = @IsComplete,
    DeviceReadingID = @DeviceReadingID,
    ModifiedDateTimeUTC = CURRENT_TIMESTAMP
WHERE
    ID = @DeviceImageID END
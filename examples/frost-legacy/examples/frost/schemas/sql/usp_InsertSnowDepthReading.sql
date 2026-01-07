CREATE PROCEDURE
    [dbo].[usp_InsertSnowDepthReading] @VendorDeviceID VARCHAR(50),
    @DistanceMm SMALLINT,
    @BatteryMv INTEGER,
    @RssiPower SMALLINT,
    @Version INTEGER,
    @TemperatureC SMALLINT,
    @ReferenceDepthMm SMALLINT,
    @Reserved1 SMALLINT,
    @Reserved2 SMALLINT,
    @Error TINYINT,
    @CaptureDateTimeUTC DATETIME,
    @RWISId VARCHAR(50) = NULL,
    @ErrorCode INT out,
    @ErrorMessage VARCHAR(2000) out,
    @SnowDepthReadingID BIGINT = NULL out AS BEGIN
SET
NOCOUNT ON;

SET
ANSI_NULLS ON;

DECLARE @DeviceID BIGINT,
@RWISDeviceID BIGINT;

SET
    @ErrorCode = 0
SET
    @ErrorMessage = 'Success'
    --Step 0, Check if Device exists in DB
SELECT
    @DeviceID = d.ID
FROM
    Devices (nolock) d
WHERE
    d.VendorDeviceID = @VendorDeviceID
    -- Check if the device exists, and return error if it doesn't
    IF (@DeviceID IS NULL) BEGIN
SET
    @ErrorCode = 100
SET
    @ErrorMessage = 'Device Does not Exist in Database' RETURN @ErrorCode END IF (@RWISId IS NOT NULL) BEGIN
    -- Check if RWISDevice exists in DB
SELECT
    @RWISDeviceID = d.ID
FROM
    Devices (NOLOCK) d
WHERE
    d.VendorDeviceID = @RWISId
    -- Check if the device exists, and return error if it doesn't
    IF (@RWISDeviceID IS NULL) BEGIN
SET
    @ErrorCode = 101
SET
    @ErrorMessage = 'RWIS Device Does not Exist in Database' RETURN @ErrorCode END END
SET
    @SnowDepthReadingID = (
        SELECT
            TOP 1 ID
        FROM
            SnowDepthReadings
        WHERE
            DeviceID = @DeviceID
            AND CaptureDateTimeUTC = @CaptureDateTimeUTC
    ) IF @SnowDepthReadingID IS NULL BEGIN
INSERT INTO
    SnowDepthReadings (
        DeviceID,
        DistanceMm,
        BatteryMv,
        RssiPower,
        Version,
        TemperatureC,
        ReferenceDepthMm,
        Reserved1,
        Reserved2,
        Error,
        CaptureDateTimeUTC,
        UploadedByRWIS
    )
VALUES
    (
        @DeviceID,
        @DistanceMm,
        @BatteryMv,
        @RssiPower,
        @Version,
        @TemperatureC,
        @ReferenceDepthMm,
        @Reserved1,
        @Reserved2,
        @Error,
        @CaptureDateTimeUTC,
        @RWISDeviceID
    )
SELECT
    @SnowDepthReadingID = @@IDENTITY END END
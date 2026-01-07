CREATE PROCEDURE
    [dbo].[usp_utl_InsertDeviceImages] (
        @DeviceID BIGINT,
        @VendorImageID VARCHAR(50),
        @CorrectedVendorImageID VARCHAR(50), -- Same, unless Captured time out of range
        @IsComplete BIT,
        @CaptureDateTimeUTC DATETIME,
        @Size INT,
        @AmbientLight VARCHAR(5),
        @Contrast VARCHAR(5),
        @Brightness VARCHAR(5),
        @Exposure VARCHAR(5),
        @Resolution INT,
        @ImageUrl VARCHAR(5000),
        @DeviceImageID BIGINT OUTPUT
    ) AS BEGIN
    -- Declare a table variable to hold the affected rows
    DECLARE @AffectedRowsTable
TABLE (ID INT);

MERGE INTO
    DeviceImages AS Target USING (
        SELECT
            @DeviceID AS DeviceID,
            @VendorImageID AS VendorImageID
    ) AS Source ON Target.DeviceID = Source.DeviceID
    AND Target.VendorImageID = Source.VendorImageID
WHEN MATCHED THEN
UPDATE SET
    [DeviceID] = @DeviceID,
    [VendorImageID] = @CorrectedVendorImageID,
    [IsComplete] = @IsComplete,
    [CaptureDateTimeUTC] = @CaptureDateTimeUTC,
    [Size] = @Size,
    [AmbientLight] = @AmbientLight,
    [Contrast] = @Contrast,
    [Brightness] = @Brightness,
    [Exposure] = @Exposure,
    [Resolution] = @Resolution,
    [ImageUrl] = @ImageUrl
WHEN NOT MATCHED THEN
INSERT
    (
        [DeviceID],
        [VendorImageID],
        [IsComplete],
        [CaptureDateTimeUTC],
        [Size],
        [AmbientLight],
        [Contrast],
        [Brightness],
        [Exposure],
        [Resolution],
        [ImageUrl]
    )
VALUES
    (
        @DeviceID,
        @VendorImageID,
        @IsComplete,
        @CaptureDateTimeUTC,
        @Size,
        @AmbientLight,
        @Contrast,
        @Brightness,
        @Exposure,
        @Resolution,
        @ImageUrl
    ) OUTPUT INSERTED.ID
INTO
    @AffectedRowsTable;

-- Use an OUTPUT clause to capture the affected ID(s)
-- Retrieve the affected row's ID(s)
SELECT
    @DeviceImageID = ID
FROM
    @AffectedRowsTable;

END;
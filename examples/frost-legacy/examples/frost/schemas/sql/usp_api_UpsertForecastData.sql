CREATE PROCEDURE
    [dbo].[usp_api_UpsertForecastData] @VendorDeviceID VARCHAR(50)
    --vendor device unqiue identifier (i.e. particle device id)	
,
    @FileName VARCHAR(200),
    @cloud_cover DECIMAL(12, 4) = NULL,
    @d_prate DECIMAL(12, 4) = NULL,
    @d_rad DECIMAL(12, 4) = NULL,
    @d_sfc_t DECIMAL(12, 4) = NULL,
    @d_snod DECIMAL(12, 4) = NULL,
    @lrad DECIMAL(12, 4) = NULL,
    @prate DECIMAL(12, 4) = NULL,
    @pres DECIMAL(12, 4) = NULL,
    @ptype DECIMAL(12, 4) = NULL,
    @rad DECIMAL(12, 4) = NULL,
    @rh DECIMAL(12, 4) = NULL,
    @sfc_t DECIMAL(12, 4) = NULL,
    @snod DECIMAL(12, 4) = NULL,
    @t DECIMAL(8, 4) = NULL,
    @vbdsf DECIMAL(8, 4) = NULL,
    @wdir DECIMAL(8, 4) = NULL,
    @wspd DECIMAL(8, 4) = NULL,
    @dewpt DECIMAL(8, 4) = NULL,
    @tuned_t DECIMAL(8, 4) = NULL,
    @tuned_rh DECIMAL(8, 4) = NULL,
    @tuned_dewpt DECIMAL(8, 4) = NULL,
    @tuned_rt DECIMAL(8, 4) = NULL,
    @valid_times BIGINT = NULL,
    @obs_blend_t DECIMAL(8, 4) = NULL,
    @obs_blend_rh DECIMAL(8, 4),
    @obs_blend_dewpt DECIMAL(8, 4) = NULL,
    @obs_blend_rt DECIMAL(8, 4) = NULL,
    @window_blend_t DECIMAL(8, 4) = NULL,
    @window_blend_rh DECIMAL(8, 4) = NULL,
    @window_blend_dewpt DECIMAL(8, 4) = NULL,
    @window_blend_rt DECIMAL(8, 4) = NULL,
    @time_str DATETIME = NULL,
    @DeviceID BIGINT out, --device id for retreiving quicker and logging
    @ForecastDataID BIGINT out,
    @ForecastSummaryID BIGINT out, --Forecast Data ID for retreiving quicker and logging
    @ErrorCode INT out, --indicates status of the results
    @ErrorMessage VARCHAR(2000) out,
    @global_rc SMALLINT = NULL,
    @global_grip DECIMAL(8, 4) = NULL,
    @obs_blend_rc SMALLINT = NULL,
    @obs_blend_grip DECIMAL(8, 4) = NULL,
    @window_blend_rc SMALLINT = NULL,
    @window_blend_grip DECIMAL(8, 4) = NULL,
    @storm_mode BIT = NULL,
    @activate_storm_mode BIT out AS BEGIN
SET
NOCOUNT ON;

DECLARE @CreateDateTimeUTC DATETIME = CURRENT_TIMESTAMP,
@dateTimeInt BIGINT = 0,
@dateTimeStr VARCHAR(14),
@fileDateTime DATETIME,
@latestSummaryID BIGINT,
@latestSummaryDate DATETIME,
@stormModeInterval INT = 0
SET
    @DeviceID = 0
SET
    @ErrorCode = 999
SET
    @activate_storm_mode = 0
    -- @ForecastSummaryID checks to see if the current file has already been set as the latest ForecastSummary
    -- in the DeviceSummary table.
SELECT
    @DeviceID = d.ID,
    @latestSummaryID = ds.ForecastSummaryID
FROM
    Devices (NOLOCK) d
    LEFT OUTER JOIN DeviceSummary (NOLOCK) ds ON ds.DeviceID = d.ID
WHERE
    d.VendorDeviceID = @VendorDeviceID IF (isnull(@DeviceID, 0) = 0) BEGIN
SET
    @ErrorCode = 100
SET
    @ErrorMessage = 'Device not found by VendorDeviceID ' + @VendorDeviceID RETURN @ErrorCode END
    -- We need to parse the file name, store its data, and update the device summary and forecast summary tables
    BEGIN
SET
    @ErrorCode = 300
SET
    @ErrorMessage = 'Failed to parse file name ' + @FileName
SET
    @dateTimeStr = REPLACE(SUBSTRING(@FileName, 14, 14), '.', '')
SET
    @dateTimeInt = cast(@dateTimeStr AS BIGINT)
SET
    @fileDateTime = DATETIMEFROMPARTS(
        SUBSTRING(@dateTimeStr, 1, 4), --year
        SUBSTRING(@dateTimeStr, 5, 2), --month
        SUBSTRING(@dateTimeStr, 7, 2), --day
        SUBSTRING(@dateTimeStr, 9, 2), --hour
        SUBSTRING(@dateTimeStr, 11, 2), --minute
        0,
        0
    )
    --seconds/milliseconds
SET
    @ErrorCode = 400
SET
    @ErrorMessage = 'Failed to get latest forecast summary for: ' + @VendorDeviceID
    -- Checks to see if the current file has already been added as a Forecast Summary
SELECT
    TOP 1 @ForecastSummaryID = ID
FROM
    ForecastSummary
WHERE
    DeviceID = @DeviceID
    AND FileName = @FileName
    -- Otherwise, we insert the new Forecast Summary, we check to see if the new Forecast Summary is more recent
    -- than the latest Forecast Summary. If it's not, we return Success. If it is, we update the DeviceSummary 
    -- table to reflect the new Forecast Summary and store the raw data
    IF @ForecastSummaryID IS NULL
    AND (
        @latestSummaryID IS NULL
        OR isnull(@latestSummaryDate, '1900-01-01') < @fileDateTime
    ) BEGIN BEGIN TRAN
    -- Insert the new Forecast Summary
SET
    @ErrorMessage = 'INSERT-ForecastSummary ' + @VendorDeviceID
INSERT INTO
    ForecastSummary (DeviceID, FileName, CreateDateTimeUTC, GeneratedDateTimeUTC, FileDateTimeUTC)
VALUES
    (@DeviceID, @FileName, @CreateDateTimeUTC, @dateTimeInt, @fileDateTime)
SELECT
    @ForecastSummaryID = @@IDENTITY
    -- Update the DeviceSummary table
SET
    @ErrorMessage = 'UPDATE-DeviceSummary ' + @VendorDeviceID
UPDATE DeviceSummary
SET
    ForecastSummaryID = @ForecastSummaryID,
    ModifiedDateTimeUTC = @CreateDateTimeUTC
WHERE
    DeviceID = @DeviceID
    -- Insert the raw data
SET
    @ErrorCode = 500
SET
    @ErrorMessage = ''
    --SET success
SET
    @ErrorCode = 0
SET
    @ErrorMessage = 'SUCCESS' COMMIT TRAN END
SET
    @ErrorMessage = 'Checking for existing Forecast data in the ForecastDataRaw table'
SELECT
    @ForecastDataID = ID
FROM
    ForecastDataRaw
WHERE
    DeviceID = @DeviceID
    AND FileName = @FileName
    AND time_str = @time_str IF @ForecastDataID IS NULL BEGIN
INSERT INTO
    [dbo].[ForecastDataRaw] (
        [DeviceID],
        [FileName],
        [cloud_cover],
        [d_prate],
        [d_rad],
        [d_sfc_t],
        [d_snod],
        [lrad],
        [prate],
        [pres],
        [ptype],
        [rad],
        [rh],
        [sfc_t],
        [snod],
        [t],
        [vbdsf],
        [wdir],
        [wspd],
        [dewpt],
        [tuned_t],
        [tuned_rh],
        [tuned_dewpt],
        [tuned_rt],
        [valid_times],
        [obs_blend_t],
        [obs_blend_rh],
        [obs_blend_dewpt],
        [obs_blend_rt],
        [time_str],
        [CreatedDateTimeUTC],
        [window_blend_t],
        [window_blend_rh],
        [window_blend_dewpt],
        [window_blend_rt],
        [ForecastSummaryID],
        global_rc,
        global_grip,
        obs_blend_rc,
        obs_blend_grip,
        window_blend_rc,
        window_blend_grip,
        storm_mode
    )
VALUES
    (
        @DeviceID,
        @FileName,
        @cloud_cover,
        @d_prate,
        @d_rad,
        @d_sfc_t,
        @d_snod,
        @lrad,
        @prate,
        @pres,
        @ptype,
        @rad,
        @rh,
        @sfc_t,
        @snod,
        @t,
        @vbdsf,
        @wdir,
        @wspd,
        @dewpt,
        @tuned_t,
        @tuned_rh,
        @tuned_dewpt,
        @tuned_rt,
        @valid_times,
        @obs_blend_t,
        @obs_blend_rh,
        @obs_blend_dewpt,
        @obs_blend_rt,
        @time_str,
        @CreateDateTimeUTC,
        @window_blend_t,
        @window_blend_rh,
        @window_blend_dewpt,
        @window_blend_rt,
        @ForecastSummaryID,
        @global_rc,
        @global_grip,
        @obs_blend_rc,
        @obs_blend_grip,
        @window_blend_rc,
        @window_blend_grip,
        @storm_mode
    )
SELECT
    @ForecastDataID = @@IDENTITY END END
    --if storm mode and forecast date time is by configured 1 hour or less from now
    IF isnull(@storm_mode, 0) = 1
    AND @time_str IS NOT NULL BEGIN
SELECT
    @stormModeInterval = isnull(SettingValue, 0)
FROM
    CustomSettings (nolock) s
WHERE
    SettingCode = 'STORM_MODE_AUTO_FORECAST'
    --check device requests if already in storm mode
    IF @time_str <= dateadd(minute, @stormModeInterval * 1, CURRENT_TIMESTAMP)
    AND NOT EXISTS (
        SELECT
            TOP 1 r.ID
        FROM
            DeviceRequests (nolock) r
            JOIN CustomSettings (nolock) s ON s.SettingCode = 'STORM_MODE_AUTO_REQUEST'
        WHERE
            DeviceID = @DeviceID
            AND RequestTypeCode = 'DEVICE_REQUEST_STORM'
            AND dateadd(minute, s.SettingValue * 1, StartDateTimeUTC) >= CURRENT_TIMESTAMP
            AND ResultCode = 200
    ) BEGIN
SET
    @activate_storm_mode = 1 END END
SET
    @ErrorCode = 0
SET
    @ErrorMessage = 'SUCCESS' RETURN @ErrorCode END
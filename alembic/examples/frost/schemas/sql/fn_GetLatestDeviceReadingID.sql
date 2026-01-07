CREATE
FUNCTION [dbo].[fn_GetLatestDeviceReadingID] (@DeviceID bigint) RETURNS
TABLE AS RETURN
SELECT
    TOP 1 ID
FROM
    DeviceReadings (nolock) r
WHERE
    r.DeviceID = @DeviceID
ORDER BY
    r.CaptureDateTimeUTC DESC
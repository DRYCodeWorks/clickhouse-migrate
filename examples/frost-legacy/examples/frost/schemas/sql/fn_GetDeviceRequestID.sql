CREATE
FUNCTION [dbo].[fn_GetDeviceRequestID] (@DeviceID bigint) RETURNS
TABLE AS RETURN
SELECT
    TOP 1 r.ID AS DeviceRequestID,
    r.CreatedUserID AS CreatedUserID
FROM
    DeviceRequests (nolock) r
    LEFT OUTER JOIN DeviceRequestImages (nolock) ri ON ri.DeviceRequestID = r.ID
    LEFT OUTER JOIN DeviceImages (nolock) i ON i.ID = ri.DeviceImageID
    AND i.CreateDateTimeUTC > r.EndDateTimeUTC
WHERE
    r.DeviceID = @DeviceID
    AND RequestTypeCode in ('DEVICE_REQUEST_PHOTO', 'DEVICE_REQUEST_BURST_PHOTO')
    AND StartDateTimeUTC > dateadd(minute, -15, CURRENT_TIMESTAMP)
    AND ResultCode = 200 --success request photo
    AND i.ID IS NULL
ORDER BY
    r.ID DESC
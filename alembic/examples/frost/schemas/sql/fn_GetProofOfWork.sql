CREATE
FUNCTION [dbo].[GetProofOfWork] (@DeviceID bigint) RETURNS
TABLE AS RETURN
WITH
    ProofOfWork AS (
        SELECT
            TOP 1 ID
        FROM
            DeviceRequests (nolock)
        WHERE
            DeviceID = @DeviceID
            AND RequestTypeCode = 'EVENT_REQUEST_WORK'
            AND StartDateTimeUTC < CURRENT_TIMESTAMP
            AND EndDateTimeUTC IS NULL
        ORDER BY
            ID DESC
    ),
    ProofOfWorkCompleted AS (
        SELECT
            TOP 1 r.ID AS ID
        FROM
            DeviceRequests (nolock) r
            LEFT OUTER JOIN DeviceRequestImages (nolock) ri ON ri.DeviceRequestID = r.ID
            LEFT OUTER JOIN DeviceImages (nolock) i ON i.ID = ri.DeviceImageID
            AND i.CreateDateTimeUTC > r.EndDateTimeUTC
        WHERE
            r.DeviceID = @DeviceID
            AND RequestTypeCode = 'EVENT_REQUEST_WORK'
            AND StartDateTimeUTC < CURRENT_TIMESTAMP
            AND EndDateTimeUTC > dateadd(minute, -15, CURRENT_TIMESTAMP)
            AND i.ID IS NULL
        ORDER BY
            r.ID DESC
    )
SELECT
    CASE
        WHEN (
            SELECT
                count(*)
            FROM
                ProofOfWork
        ) > 0 THEN (
            SELECT
                TOP 1 ID
            FROM
                ProofOfWork
        )
        WHEN (
            SELECT
                count(*)
            FROM
                ProofOfWorkCompleted
        ) > 0 THEN (
            SELECT
                TOP 1 ID
            FROM
                ProofOfWorkCompleted
        )
        ELSE NULL
    END AS ID
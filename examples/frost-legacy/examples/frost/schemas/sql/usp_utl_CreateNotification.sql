CREATE PROCEDURE
    [dbo].usp_utl_CreateNotification (@DeviceID BIGINT, @DeviceRequestID BIGINT, @CreatedUserID UNIQUEIDENTIFIER) AS BEGIN
INSERT INTO
    [dbo].[Notifications] (
        [DeviceID],
        [NotificationMethodID],
        [NotificationTypeID],
        [NotificationStatusID],
        [ReferenceTypeID],
        [ReferenceKey],
        [NotifyDateTimeUTC],
        [SentDateTimeUTC],
        [Data],
        [TriggeredUserID],
        [CreateDateTimeUTC]
    )
VALUES
    (
        @DeviceID,
        3 --WEB
,
        4 --REQUEST_PHOTO_COMPLETED
,
        1 --NEW
,
        2 --DEVICEREQUESTS_ID
,
        @DeviceRequestID,
        CURRENT_TIMESTAMP,
        NULL,
        NULL,
        @CreatedUserID,
        CURRENT_TIMESTAMP
    ) END
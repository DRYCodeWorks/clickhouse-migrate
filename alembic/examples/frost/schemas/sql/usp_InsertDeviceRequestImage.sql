CREATE PROCEDURE
    [dbo].usp_InsertDeviceRequestImage (@DeviceRequestID BIGINT, @DeviceImageID BIGINT) AS BEGIN
INSERT INTO
    DeviceRequestImages (DeviceRequestID, DeviceImageID)
VALUES
    (@DeviceRequestID, @DeviceImageID) END
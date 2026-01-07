CREATE
FUNCTION get_device_type_name (@DeviceID BIGINT) RETURNS VARCHAR(200) AS BEGIN RETURN (
    SELECT
        DeviceType.Name
    FROM
        DeviceType
        JOIN Devices ON DeviceType.ID = Devices.DeviceType
    WHERE
        Devices.ID = @DeviceID
) END
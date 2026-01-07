Create or REPLACE TABLE sds_readings
(
    ID UInt64 CODEC(Delta, ZSTD),
    DeviceID UInt32 CODEC(T64),
    UploadedByRWIS UInt32 CODEC(T64),
    CreatedDateTimeUTC DateTime64 CODEC(Delta, ZSTD),
    CaptureDateTimeUTC DateTime64 CODEC(Delta, ZSTD),
    Version UInt8,
    Error UInt8,
    DistanceMm Int16,
    BatteryMv UInt16,
    RssiPower Int8,
    TemperatureC Int16,
    ReferenceDepthMm UInt16,
    Reserved1 Int16,
    Reserved2 Int16

)
ENGINE = ReplacingMergeTree()
ORDER BY (DeviceID, CaptureDateTimeUTC)
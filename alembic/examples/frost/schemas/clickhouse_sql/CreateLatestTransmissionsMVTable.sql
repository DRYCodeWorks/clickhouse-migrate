CREATE TABLE latest_transmissions (
	ID UInt64 CODEC(Delta, ZSTD),
    DeviceID UInt32 CODEC(T64),
    VendorDeviceID LowCardinality(String),
    CaptureTimestampUTC DateTime CODEC(Delta, ZSTD),
    CaptureDateTimeUTC DateTime64(3) CODEC(Delta, ZSTD),
    SurfaceTemp Decimal(6, 2),
    AirTemp Decimal(5, 2),
    DewPoint Decimal(5, 2),
    Humidity Decimal(4, 2),
    CreatedDateTimeUTC DateTime64(3) CODEC(Delta, ZSTD),
    HeaterTemp Decimal(6, 2),
    AmbientLight Int32
) ENGINE = ReplacingMergeTree(CaptureDateTimeUTC)
ORDER BY (
		DeviceID
	)
PARTITION BY toStartOfMonth(CaptureDateTimeUTC)
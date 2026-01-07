CREATE OR REPLACE TABLE transmissions (
	ID UInt64 CODEC(Delta, ZSTD),
	DeviceID UInt32 CODEC(T64),
	VendorDeviceID LowCardinality(String),
	CaptureTimestampUTC DATETIME CODEC(Delta, ZSTD),
	CaptureDateTimeUTC DateTime64 CODEC(Delta, ZSTD),
	SurfaceTemp DECIMAL(6, 2),
	AirTemp DECIMAL(5, 2),
	DewPoint DECIMAL(5, 2),
	Humidity DECIMAL(4, 2),
	CreatedDateTimeUTC DateTime64 CODEC(Delta, ZSTD),
	HeaterTemp DECIMAL(6, 2),
	AmbientLight Int32
) ENGINE = ReplacingMergeTree()
ORDER BY (
		DeviceID,
		CaptureDateTimeUTC
	)
PARTITION BY toStartOfMonth(CaptureDateTimeUTC)
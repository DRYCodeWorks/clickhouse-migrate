CREATE TABLE images_new
(
    `DeviceID` UInt32,
    `VendorImageID` String,
    `CameraVersion` LowCardinality(String),
    `VendorDeviceID` LowCardinality(String),
    `CaptureTimestampUTC` DateTime CODEC(Delta(4), ZSTD(1)),
    `ImageBucket` LowCardinality(String),
    `ImageFormat` LowCardinality(String),
    `ModifiedDateTimeUTC` DateTime64(3) CODEC(Delta(8), ZSTD(1)),
    `CreatedDateTimeUTC` DateTime64(3) CODEC(Delta(8), ZSTD(1)),
    `CaptureDateTimeUTC` DateTime64(3) CODEC(Delta(8), ZSTD(1)),
    `ImageAssembledDateTimeUTC` DateTime64(3) CODEC(Delta(8), ZSTD(1)),
    `CVAssessmentDateTimeUTC` DateTime64(3) CODEC(Delta(8), ZSTD(1)),
    `IsComplete` Bool,
    `AmbientLight` Int32,
    `Contrast` UInt8,
    `Brightness` UInt8,
    `Exposure` UInt8,
    `Resolution` UInt8,
    `ImageUrl` String,
    `TransmissionCaptureDateTimeUTC` DateTime64(3) CODEC(Delta(8), ZSTD(1)),
    `ImageID` UInt32 CODEC(Delta(4), ZSTD(1)),
    `NightClearPavement` Decimal(4, 2),
    `NightSnowing` Decimal(4, 2),
    `NightWetPavement` Decimal(4, 2),
    `NightSnowOnRoad` Decimal(4, 2),
    `NightPartialSnowOnRoad` Decimal(4, 2),
    `DaySnowing` Decimal(4, 2),
    `DayPartialSnowOnRoad` Decimal(4, 2),
    `DayClearPavement` Decimal(4, 2),
    `DayWetPavement` Decimal(4, 2),
    `DaySnowOnRoad` Decimal(4, 2),
    `Night` Decimal(4, 2),
    `Sunny` Decimal(4, 2),
    `Cloudy` Decimal(4, 2),
    `ClearPavement` Decimal(4, 2),
    `WetPavement` Decimal(4, 2),
    `SnowOnRoad` Decimal(4, 2),
    `PartialSnowOnRoad` Decimal(4, 2),
    `Snowing` Decimal(4, 2),
    `Raining` Decimal(4, 2),
    `ModelVersion` LowCardinality(String),
    `IcedLens` Decimal(4, 2),
    `Version` Int8,
    `IsBurstImage` Bool,
    PROJECTION image_url (
        SELECT * ORDER BY ImageUrl
    )
)
ENGINE = ReplacingMergeTree(Version)
PARTITION BY toStartOfMonth(CaptureDateTimeUTC)
ORDER BY (DeviceID, CaptureDateTimeUTC)
SETTINGS deduplicate_merge_projection_mode = 'rebuild';

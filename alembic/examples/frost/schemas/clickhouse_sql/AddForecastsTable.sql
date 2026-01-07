CREATE TABLE forecasts
(
    `DeviceID` UInt32,
    `CaptureDateTimeUTC` DateTime64(3) CODEC(Delta, ZSTD),
    `ForecastDateTimeUTC` DateTime64(3) CODEC(Delta, ZSTD),
    `SurfaceTemp` Decimal(5, 2) CODEC(ZSTD(3)),
    `AirTemp` Decimal(5, 2) CODEC(ZSTD(3)),
    `DewPoint` Decimal(4, 2) CODEC(ZSTD(3)),
    `Humidity` Decimal(4, 2) CODEC(ZSTD(3)),
    `SurfaceGrip` Decimal(2, 2) CODEC(ZSTD(3)),
    `RoadCondition` Int8,
    `PrecipType` Int8,
    `PrecipRate` Decimal(5, 2) CODEC(ZSTD(3)),
    `WindDirection` Int16 CODEC(Delta, ZSTD),
    `WindSpeed` Decimal(5, 2) CODEC(ZSTD(3)),
    `CloudCover` Int8,
    `ProbPrecip` Decimal(4, 2) CODEC(ZSTD(3)),
    `CprobRain` Decimal(4, 2) CODEC(ZSTD(3)),
    `CprobSnow` Decimal(4, 2) CODEC(ZSTD(3)),
    `CprobIce` Decimal(4, 2) CODEC(ZSTD(3)),
    `PrecipAccumTotal` Decimal(5, 2) CODEC(ZSTD(3)),
    `SnowAccumTotal` Decimal(5, 2) CODEC(ZSTD(3)),
    `BlowingSnowPotential` Int8,
    `PavementSnowDepth` Decimal(5, 2) CODEC(ZSTD(3)),
    `Visibility` Int8,
    `Slickness` Int8
)
ENGINE = MergeTree()
PARTITION BY toStartOfMonth(CaptureDateTimeUTC)
ORDER BY (DeviceID, CaptureDateTimeUTC, ForecastDateTimeUTC)

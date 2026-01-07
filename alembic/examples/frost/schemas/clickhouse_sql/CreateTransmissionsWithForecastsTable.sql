-- Table combining transmission data with matching forecast data
-- All temperature values are normalized to Fahrenheit for consistency
-- Forecast temperatures are converted from Celsius to Fahrenheit during insert
-- Client-facing table for analytics and error calculations
CREATE OR REPLACE TABLE transmissions_with_forecasts
(
    -- Transmission fields (never null, already in Fahrenheit)
    ID UInt64 CODEC(Delta, ZSTD),
    DeviceID UInt32 CODEC(T64),
    VendorDeviceID LowCardinality(String),
    CaptureTimestampUTC DateTime CODEC(Delta, ZSTD),
    CaptureDateTimeUTC DateTime64(3) CODEC(Delta, ZSTD),
    CreatedDateTimeUTC DateTime64(3) CODEC(Delta, ZSTD),
    
    -- Transmission temperature fields in Fahrenheit
    SurfaceTemp_F Decimal(6, 2) CODEC(ZSTD(3)),
    AirTemp_F Decimal(5, 2) CODEC(ZSTD(3)),
    DewPoint_F Decimal(5, 2) CODEC(ZSTD(3)),
    HeaterTemp_F Decimal(5, 2) CODEC(ZSTD(3)),
    
    -- Non-temperature transmission fields
    Humidity Decimal(4, 2) CODEC(ZSTD(3)),  -- Percentage (no unit conversion needed)
    AmbientLight UInt32,
    
    -- Forecast metadata fields
    ForecastDateTimeUTC Nullable(DateTime64(3)) CODEC(Delta, ZSTD),
    ForecastAge_Seconds Nullable(UInt32),
    
    -- Forecast weather fields (can be null)
    WindSpeed Nullable(Decimal(5, 2)) CODEC(ZSTD(3)),
    WindDirection Nullable(Int16) CODEC(Delta, ZSTD),
    SurfaceGrip Nullable(Decimal(2, 2)) CODEC(ZSTD(3)),
    RoadCondition Nullable(Int8),
    Slickness Nullable(Int8),
    PrecipType Nullable(Int8),
    PrecipRate Nullable(Decimal(5, 2)) CODEC(ZSTD(3)),
    CloudCover Nullable(Int8),
    Visibility Nullable(Int8),
    ProbPrecip Nullable(Decimal(4, 2)) CODEC(ZSTD(3)),
    CprobRain Nullable(Decimal(4, 2)) CODEC(ZSTD(3)),
    CprobSnow Nullable(Decimal(4, 2)) CODEC(ZSTD(3)),
    CprobIce Nullable(Decimal(4, 2)) CODEC(ZSTD(3)),
    PrecipAccumTotal Nullable(Decimal(5, 2)) CODEC(ZSTD(3)),
    SnowAccumTotal Nullable(Decimal(5, 2)) CODEC(ZSTD(3)),
    BlowingSnowPotential Nullable(Int8),
    PavementSnowDepth Nullable(Decimal(5, 2)) CODEC(ZSTD(3)),
    
    -- Forecast temperature fields (converted to Fahrenheit from Celsius source)
    ForecastSurfaceTemp_F Nullable(Decimal(5, 2)) CODEC(ZSTD(3)),
    ForecastAirTemp_F Nullable(Decimal(5, 2)) CODEC(ZSTD(3)),
    ForecastDewPoint_F Nullable(Decimal(4, 2)) CODEC(ZSTD(3)),
    ForecastHumidity Nullable(Decimal(4, 2)) CODEC(ZSTD(3)),  -- Percentage (no conversion needed)
    
    -- Materialized columns for error calculations (Fahrenheit - Fahrenheit)
    SurfaceTempError_F Nullable(Decimal(5, 2)) MATERIALIZED IF(ForecastSurfaceTemp_F IS NOT NULL, 
                                                                SurfaceTemp_F - ForecastSurfaceTemp_F, 
                                                                NULL),
    AirTempError_F Nullable(Decimal(5, 2)) MATERIALIZED IF(ForecastAirTemp_F IS NOT NULL, 
                                                            AirTemp_F - ForecastAirTemp_F, 
                                                            NULL),
    DewPointError_F Nullable(Decimal(5, 2)) MATERIALIZED IF(ForecastDewPoint_F IS NOT NULL, 
                                                             DewPoint_F - ForecastDewPoint_F, 
                                                             NULL),
    HumidityError Nullable(Decimal(4, 2)) MATERIALIZED IF(ForecastHumidity IS NOT NULL, 
                                                           Humidity - ForecastHumidity, 
                                                           NULL)
)
ENGINE = ReplacingMergeTree(CreatedDateTimeUTC)
ORDER BY (DeviceID, CaptureDateTimeUTC)
PARTITION BY toYYYYMM(CaptureDateTimeUTC)
TTL CaptureDateTimeUTC + INTERVAL 90 DAY
SETTINGS index_granularity = 8192
COMMENT 'Transmission data enriched with matching forecast data. All temperatures in Fahrenheit. Client-facing table.'
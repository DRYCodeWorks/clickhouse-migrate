-- ================================================================================================
-- best_known_forecasts: Critical Deduplication Layer for Forecast Data
-- ================================================================================================
-- 
-- PURPOSE:
-- This table serves as a crucial deduplication layer in the forecast data pipeline.
-- It ensures that for each (DeviceID, ForecastDateTimeUTC) pair, only the most recent
-- forecast is retained, preventing duplicate or outdated forecasts from propagating
-- through the system.
--
-- WHY THIS TABLE EXISTS:
-- 1. Forecast Updates: Weather forecasts are continuously updated. A forecast for 2PM tomorrow
--    might be issued at 8AM today, then updated at noon with better data. We only want
--    the latest (most accurate) forecast.
-- 
-- 2. ASOF JOIN Optimization: The _mv_transmissions_forecast_joiner uses ASOF JOIN to match
--    transmissions with forecasts. Having deduplicated data ensures the join finds the
--    single best forecast match without ambiguity.
--
-- 3. Storage Efficiency: Eliminates redundant forecast data, keeping only what's needed.
--
-- HOW IT WORKS:
-- - ReplacingMergeTree engine with LatestCaptureDateTimeUTC as the version column
-- - When multiple rows have the same (DeviceID, ForecastDateTimeUTC), only the row
--   with the maximum LatestCaptureDateTimeUTC is kept during merge operations
-- - Fed by _mv_forecasts_deduplicator materialized view from the raw forecasts table
--
-- DATA FLOW:
-- forecasts (raw) → _mv_forecasts_deduplicator → best_known_forecasts (this table)
--                                                           ↓
--                                   _mv_transmissions_forecast_joiner (uses for ASOF JOIN)
--                                                           ↓
--                                              transmissions_with_forecasts
--
-- TEMPERATURE UNITS:
-- All temperature fields stored in Celsius (as received from forecast source)
-- Conversion to Fahrenheit happens in _mv_transmissions_forecast_joiner
--
-- IMPORTANT: This is an internal table - clients should not query directly
CREATE OR REPLACE TABLE best_known_forecasts
(
    DeviceID UInt32 CODEC(T64),
    ForecastDateTimeUTC DateTime64(3) CODEC(Delta, ZSTD),
    LatestCaptureDateTimeUTC DateTime64(3) CODEC(Delta, ZSTD),
    
    -- Temperature fields in Celsius
    SurfaceTemp_C Decimal(5, 2) CODEC(ZSTD(3)),
    AirTemp_C Decimal(5, 2) CODEC(ZSTD(3)),
    DewPoint_C Decimal(4, 2) CODEC(ZSTD(3)),
    
    -- Non-temperature fields
    Humidity Decimal(4, 2) CODEC(ZSTD(3)),
    SurfaceGrip Decimal(2, 2) CODEC(ZSTD(3)),
    RoadCondition Int8,
    PrecipType Int8,
    PrecipRate Decimal(5, 2) CODEC(ZSTD(3)),
    WindDirection Int16 CODEC(Delta, ZSTD),
    WindSpeed Decimal(5, 2) CODEC(ZSTD(3)),
    CloudCover Int8,
    ProbPrecip Decimal(4, 2) CODEC(ZSTD(3)),
    CprobRain Decimal(4, 2) CODEC(ZSTD(3)),
    CprobSnow Decimal(4, 2) CODEC(ZSTD(3)),
    CprobIce Decimal(4, 2) CODEC(ZSTD(3)),
    PrecipAccumTotal Decimal(5, 2) CODEC(ZSTD(3)),
    SnowAccumTotal Decimal(5, 2) CODEC(ZSTD(3)),
    BlowingSnowPotential Int8,
    PavementSnowDepth Decimal(5, 2) CODEC(ZSTD(3)),
    Visibility Int8,
    Slickness Int8
)
ENGINE = ReplacingMergeTree(LatestCaptureDateTimeUTC)
ORDER BY (DeviceID, ForecastDateTimeUTC)
PARTITION BY toYYYYMM(ForecastDateTimeUTC)
SETTINGS index_granularity = 4096
COMMENT 'Internal deduplicated forecast data. ReplacingMergeTree keeps latest version. Temperatures in Celsius.'
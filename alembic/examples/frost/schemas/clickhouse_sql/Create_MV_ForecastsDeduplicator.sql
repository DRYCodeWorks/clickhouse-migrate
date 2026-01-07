-- Materialized view that feeds deduplicated forecast data
-- Transforms forecast data into best_known_forecasts with proper column names
CREATE MATERIALIZED VIEW _mv_forecasts_deduplicator
TO best_known_forecasts
AS
SELECT 
    DeviceID,
    ForecastDateTimeUTC,
    CaptureDateTimeUTC AS LatestCaptureDateTimeUTC,
    
    -- Temperature fields in Celsius from source
    SurfaceTemp AS SurfaceTemp_C,
    AirTemp AS AirTemp_C,
    DewPoint AS DewPoint_C,
    
    -- Non-temperature fields
    Humidity,
    SurfaceGrip,
    RoadCondition,
    PrecipType,
    PrecipRate,
    WindDirection,
    WindSpeed,
    CloudCover,
    ProbPrecip,
    CprobRain,
    CprobSnow,
    CprobIce,
    PrecipAccumTotal,
    SnowAccumTotal,
    BlowingSnowPotential,
    PavementSnowDepth,
    Visibility,
    Slickness
FROM forecasts
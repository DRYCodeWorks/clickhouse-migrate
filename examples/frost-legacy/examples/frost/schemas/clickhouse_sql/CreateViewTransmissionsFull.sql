-- Client-facing view providing full transmission data
-- Combines enriched transmissions (with forecasts) and base transmissions
-- All temperature values in Fahrenheit for consistency
CREATE OR REPLACE VIEW v_transmissions_full AS
SELECT 
    ID,
    DeviceID,
    VendorDeviceID,
    CaptureTimestampUTC,
    CaptureDateTimeUTC,
    CreatedDateTimeUTC,
    SurfaceTemp_F,
    AirTemp_F,
    DewPoint_F,
    Humidity,
    HeaterTemp_F,
    AmbientLight,
    ForecastDateTimeUTC,
    ForecastAge_Seconds,
    WindSpeed,
    WindDirection,
    SurfaceGrip,
    RoadCondition,
    Slickness,
    PrecipType,
    PrecipRate,
    CloudCover,
    Visibility,
    ProbPrecip,
    CprobRain,
    CprobSnow,
    CprobIce,
    PrecipAccumTotal,
    SnowAccumTotal,
    BlowingSnowPotential,
    PavementSnowDepth,
    ForecastSurfaceTemp_F,
    ForecastAirTemp_F,
    ForecastDewPoint_F,
    ForecastHumidity,
    SurfaceTempError_F,
    AirTempError_F,
    DewPointError_F,
    HumidityError,
    'with_forecast' as source_table
FROM transmissions_with_forecasts
WHERE 
    DeviceID in {device_ids:Array(UInt32)} 
    AND
    CaptureDateTimeUTC BETWEEN {start_time:DateTime64} AND {end_time:DateTime64}
    AND 
    CaptureDateTimeUTC >= (SELECT min(CaptureDateTimeUTC) + Interval 1 Day FROM transmissions_with_forecasts)
UNION ALL
-- Base transmissions for historical data before enrichment began
SELECT 
    ID,
    DeviceID,
    VendorDeviceID,
    CaptureTimestampUTC,
    CaptureDateTimeUTC,
    CreatedDateTimeUTC,
    SurfaceTemp AS SurfaceTemp_F,  -- Already in Fahrenheit
    AirTemp AS AirTemp_F,
    DewPoint AS DewPoint_F,
    Humidity,
    HeaterTemp AS HeaterTemp_F,
    AmbientLight,
    NULL AS ForecastDateTimeUTC,
    NULL AS ForecastAge_Seconds,
    NULL AS WindSpeed,
    NULL AS WindDirection,
    NULL AS SurfaceGrip,
    NULL AS RoadCondition,
    NULL AS Slickness,
    NULL AS PrecipType,
    NULL AS PrecipRate,
    NULL AS CloudCover,
    NULL AS Visibility,
    NULL AS ProbPrecip,
    NULL AS CprobRain,
    NULL AS CprobSnow,
    NULL AS CprobIce,
    NULL AS PrecipAccumTotal,
    NULL AS SnowAccumTotal,
    NULL AS BlowingSnowPotential,
    NULL AS PavementSnowDepth,
    NULL AS ForecastSurfaceTemp_F,
    NULL AS ForecastAirTemp_F,
    NULL AS ForecastDewPoint_F,
    NULL AS ForecastHumidity,
    NULL AS SurfaceTempError_F,
    NULL AS AirTempError_F,
    NULL AS DewPointError_F,
    NULL AS HumidityError,
    'base' as source_table
FROM transmissions FINAL
WHERE 
    DeviceID in {device_ids:Array(UInt32)} 
    AND
    CaptureDateTimeUTC BETWEEN {start_time:DateTime64} AND {end_time:DateTime64}
    AND
    CaptureDateTimeUTC < (SELECT min(CaptureDateTimeUTC) + Interval 1 Day FROM transmissions_with_forecasts)
COMMENT 'Full transmission data with optional forecast enrichment. All temperatures in Fahrenheit.'
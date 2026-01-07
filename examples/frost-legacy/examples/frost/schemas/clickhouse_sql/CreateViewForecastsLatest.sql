-- Client-facing view for accessing the latest forecast data
-- Now uses ReplacingMergeTree table directly instead of AggregatingMergeTree
-- Returns forecast values with temperatures in Celsius
CREATE OR REPLACE VIEW v_forecasts_latest
AS SELECT
    DeviceID,
    ForecastDateTimeUTC,
    LatestCaptureDateTimeUTC,
    
    -- Temperature fields in Celsius
    SurfaceTemp_C,
    AirTemp_C,
    DewPoint_C,
    
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
FROM best_known_forecasts
FINAL  -- FINAL modifier ensures ReplacingMergeTree returns only the latest version
WHERE (DeviceID IN ({device_ids:Array(UInt32)})) 
    AND ((ForecastDateTimeUTC >= coalesce({start_time:Nullable(DateTime64)}, now() - toIntervalDay(1))) 
    AND (ForecastDateTimeUTC <= coalesce({end_time:Nullable(DateTime64)}, now())))
ORDER BY
    DeviceID ASC,
    LatestCaptureDateTimeUTC DESC
COMMENT 'Latest forecast data per device using ReplacingMergeTree. Temperatures in Celsius.'
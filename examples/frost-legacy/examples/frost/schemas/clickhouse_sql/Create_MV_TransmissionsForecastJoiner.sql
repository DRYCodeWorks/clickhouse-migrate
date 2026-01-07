-- Materialized view that joins transmission data with forecast data
-- Converts forecast temperatures from Celsius to Fahrenheit during join
CREATE MATERIALIZED VIEW _mv_transmissions_forecast_joiner
TO transmissions_with_forecasts
AS
SELECT 
    -- Transmission base fields (already in Fahrenheit)
    t.ID,
    t.DeviceID,
    t.VendorDeviceID,
    t.CaptureTimestampUTC,
    t.CaptureDateTimeUTC,
    t.CreatedDateTimeUTC,
    
    -- Transmission temperature fields (already in Fahrenheit)
    t.SurfaceTemp AS SurfaceTemp_F,
    t.AirTemp AS AirTemp_F,
    t.DewPoint AS DewPoint_F,
    t.HeaterTemp AS HeaterTemp_F,
    
    -- Non-temperature transmission fields
    t.Humidity,
    t.AmbientLight,
    
    -- Forecast metadata using :: operator for cleaner syntax
    IF(f.ForecastDateTimeUTC >= '2022-01-01', 
       f.ForecastDateTimeUTC, 
       NULL)::Nullable(DateTime64(3)) AS ForecastDateTimeUTC,
    
    IF(f.ForecastDateTimeUTC >= '2022-01-01',
       toUInt32(abs(toUnixTimestamp64Milli(t.CaptureDateTimeUTC) - 
                    toUnixTimestamp64Milli(f.ForecastDateTimeUTC)) / 1000),
       NULL)::Nullable(UInt32) AS ForecastAge_Seconds,
    
    -- Non-temperature forecast fields
    IF(f.ForecastDateTimeUTC >= '2022-01-01', f.WindSpeed, NULL)::Nullable(Decimal(5, 2)) AS WindSpeed,
    IF(f.ForecastDateTimeUTC >= '2022-01-01', f.WindDirection, NULL)::Nullable(Int16) AS WindDirection,
    IF(f.ForecastDateTimeUTC >= '2022-01-01', f.SurfaceGrip, NULL)::Nullable(Decimal(2, 2)) AS SurfaceGrip,
    IF(f.ForecastDateTimeUTC >= '2022-01-01', f.RoadCondition, NULL)::Nullable(Int8) AS RoadCondition,
    IF(f.ForecastDateTimeUTC >= '2022-01-01', f.Slickness, NULL)::Nullable(Int8) AS Slickness,
    IF(f.ForecastDateTimeUTC >= '2022-01-01', f.PrecipType, NULL)::Nullable(Int8) AS PrecipType,
    IF(f.ForecastDateTimeUTC >= '2022-01-01', f.PrecipRate, NULL)::Nullable(Decimal(5, 2)) AS PrecipRate,
    IF(f.ForecastDateTimeUTC >= '2022-01-01', f.CloudCover, NULL)::Nullable(Int8) AS CloudCover,
    IF(f.ForecastDateTimeUTC >= '2022-01-01', f.Visibility, NULL)::Nullable(Int8) AS Visibility,
    IF(f.ForecastDateTimeUTC >= '2022-01-01', f.ProbPrecip, NULL)::Nullable(Decimal(4, 2)) AS ProbPrecip,
    IF(f.ForecastDateTimeUTC >= '2022-01-01', f.CprobRain, NULL)::Nullable(Decimal(4, 2)) AS CprobRain,
    IF(f.ForecastDateTimeUTC >= '2022-01-01', f.CprobSnow, NULL)::Nullable(Decimal(4, 2)) AS CprobSnow,
    IF(f.ForecastDateTimeUTC >= '2022-01-01', f.CprobIce, NULL)::Nullable(Decimal(4, 2)) AS CprobIce,
    IF(f.ForecastDateTimeUTC >= '2022-01-01', f.PrecipAccumTotal, NULL)::Nullable(Decimal(5, 2)) AS PrecipAccumTotal,
    IF(f.ForecastDateTimeUTC >= '2022-01-01', f.SnowAccumTotal, NULL)::Nullable(Decimal(5, 2)) AS SnowAccumTotal,
    IF(f.ForecastDateTimeUTC >= '2022-01-01', f.BlowingSnowPotential, NULL)::Nullable(Int8) AS BlowingSnowPotential,
    IF(f.ForecastDateTimeUTC >= '2022-01-01', f.PavementSnowDepth, NULL)::Nullable(Decimal(5, 2)) AS PavementSnowDepth,
    
    -- Temperature conversions from Celsius to Fahrenheit
    -- Using the best_known_forecasts table which has _C suffix columns
    IF(f.ForecastDateTimeUTC >= '2022-01-01', 
       (f.SurfaceTemp_C * 9/5) + 32, 
       NULL)::Nullable(Decimal(5, 2)) AS ForecastSurfaceTemp_F,
       
    IF(f.ForecastDateTimeUTC >= '2022-01-01', 
       (f.AirTemp_C * 9/5) + 32, 
       NULL)::Nullable(Decimal(5, 2)) AS ForecastAirTemp_F,
       
    IF(f.ForecastDateTimeUTC >= '2022-01-01', 
       (f.DewPoint_C * 9/5) + 32, 
       NULL)::Nullable(Decimal(4, 2)) AS ForecastDewPoint_F,
       
    IF(f.ForecastDateTimeUTC >= '2022-01-01', 
       f.Humidity, 
       NULL)::Nullable(Decimal(4, 2)) AS ForecastHumidity
    
FROM transmissions t
ASOF LEFT JOIN best_known_forecasts f
    ON t.DeviceID = f.DeviceID 
    AND t.CaptureDateTimeUTC >= f.ForecastDateTimeUTC
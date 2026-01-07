"""hydrate_forecast_tables

Revision ID: 3a9f7c2d8e5b
Revises: 037607b704ed
Create Date: 2025-08-29 14:04:00.000000

"""

import sqlalchemy as sa
from alembic import op

from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "3a9f7c2d8e5b"
down_revision = "037607b704ed"  # Points to create_transmissions_unified_view
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Hydrate the forecast and transmission tables with recent data."""

    # Process in batches to avoid memory limits
    time_intervals = [
        (72, 60),  # 3 days to 60 hours ago
        (60, 48),  # 60 to 48 hours ago
        (48, 36),  # 48 to 36 hours ago
        (36, 24),  # 36 to 24 hours ago
        (24, 12),  # 24 to 12 hours ago
        (12, 6),  # 12 to 6 hours ago
        (6, 0),  # Last 6 hours
    ]

    # Step 1: Hydrate best_known_forecasts with deduplicated values in batches
    print("Hydrating best_known_forecasts table in batches...")
    for start_hours, end_hours in time_intervals:
        print(f"  Processing {start_hours} to {end_hours} hours ago...")
        query = f"""
        INSERT INTO best_known_forecasts
        SELECT
            DeviceID,
            ForecastDateTimeUTC,
            CaptureDateTimeUTC AS LatestCaptureDateTimeUTC,
            SurfaceTemp AS SurfaceTemp_C,
            AirTemp AS AirTemp_C,
            DewPoint AS DewPoint_C,
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
        FROM (
            SELECT *
            FROM forecasts
            WHERE ForecastDateTimeUTC >= now() - INTERVAL {start_hours} HOUR
              AND ForecastDateTimeUTC < now() - INTERVAL {end_hours} HOUR
            ORDER BY DeviceID, ForecastDateTimeUTC, CaptureDateTimeUTC DESC
        )
        SETTINGS max_memory_usage = 5000000000
        """
        op.execute(query)

    # Step 2: Hydrate transmissions_with_forecasts - use smaller batch due to JOIN
    print("Hydrating transmissions_with_forecasts table in smaller batches...")
    for start_hours, end_hours in time_intervals:  # Only last 12 hours for heavy JOIN
        print(f"  Processing {start_hours} to {end_hours} hours ago...")
        op.execute(
            f"""
        INSERT INTO transmissions_with_forecasts
        SELECT 
            t.ID,
            t.DeviceID,
            t.VendorDeviceID,
            t.CaptureTimestampUTC,
            t.CaptureDateTimeUTC,
            t.CreatedDateTimeUTC,
            t.SurfaceTemp AS SurfaceTemp_F,
            t.AirTemp AS AirTemp_F,
            t.DewPoint AS DewPoint_F,
            t.HeaterTemp AS HeaterTemp_F,
            t.Humidity,
            t.AmbientLight,
            IF(f.ForecastDateTimeUTC >= '2022-01-01', f.ForecastDateTimeUTC, NULL) AS ForecastDateTimeUTC,
            IF(f.ForecastDateTimeUTC >= '2022-01-01',
               toUInt32(abs(toUnixTimestamp64Milli(t.CaptureDateTimeUTC) - 
                            toUnixTimestamp64Milli(f.ForecastDateTimeUTC)) / 1000),
               NULL) AS ForecastAge_Seconds,
            IF(f.ForecastDateTimeUTC >= '2022-01-01', f.WindSpeed, NULL) AS WindSpeed,
            IF(f.ForecastDateTimeUTC >= '2022-01-01', f.WindDirection, NULL) AS WindDirection,
            IF(f.ForecastDateTimeUTC >= '2022-01-01', f.SurfaceGrip, NULL) AS SurfaceGrip,
            IF(f.ForecastDateTimeUTC >= '2022-01-01', f.RoadCondition, NULL) AS RoadCondition,
            IF(f.ForecastDateTimeUTC >= '2022-01-01', f.Slickness, NULL) AS Slickness,
            IF(f.ForecastDateTimeUTC >= '2022-01-01', f.PrecipType, NULL) AS PrecipType,
            IF(f.ForecastDateTimeUTC >= '2022-01-01', f.PrecipRate, NULL) AS PrecipRate,
            IF(f.ForecastDateTimeUTC >= '2022-01-01', f.CloudCover, NULL) AS CloudCover,
            IF(f.ForecastDateTimeUTC >= '2022-01-01', f.Visibility, NULL) AS Visibility,
            IF(f.ForecastDateTimeUTC >= '2022-01-01', f.ProbPrecip, NULL) AS ProbPrecip,
            IF(f.ForecastDateTimeUTC >= '2022-01-01', f.CprobRain, NULL) AS CprobRain,
            IF(f.ForecastDateTimeUTC >= '2022-01-01', f.CprobSnow, NULL) AS CprobSnow,
            IF(f.ForecastDateTimeUTC >= '2022-01-01', f.CprobIce, NULL) AS CprobIce,
            IF(f.ForecastDateTimeUTC >= '2022-01-01', f.PrecipAccumTotal, NULL) AS PrecipAccumTotal,
            IF(f.ForecastDateTimeUTC >= '2022-01-01', f.SnowAccumTotal, NULL) AS SnowAccumTotal,
            IF(f.ForecastDateTimeUTC >= '2022-01-01', f.BlowingSnowPotential, NULL) AS BlowingSnowPotential,
            IF(f.ForecastDateTimeUTC >= '2022-01-01', f.PavementSnowDepth, NULL) AS PavementSnowDepth,
            IF(f.ForecastDateTimeUTC >= '2022-01-01', (f.SurfaceTemp_C * 9/5) + 32, NULL) AS ForecastSurfaceTemp_F,
            IF(f.ForecastDateTimeUTC >= '2022-01-01', (f.AirTemp_C * 9/5) + 32, NULL) AS ForecastAirTemp_F,
            IF(f.ForecastDateTimeUTC >= '2022-01-01', (f.DewPoint_C * 9/5) + 32, NULL) AS ForecastDewPoint_F,
            IF(f.ForecastDateTimeUTC >= '2022-01-01', f.Humidity, NULL) AS ForecastHumidity
        FROM transmissions t
        ASOF LEFT JOIN best_known_forecasts f
            ON t.DeviceID = f.DeviceID 
            AND t.CaptureDateTimeUTC >= f.ForecastDateTimeUTC
        WHERE t.CaptureDateTimeUTC >= now() - INTERVAL {start_hours} HOUR
          AND t.CaptureDateTimeUTC < now() - INTERVAL {end_hours} HOUR
        SETTINGS max_memory_usage = 5000000000
        """
        )

    print("Data hydration complete!")


def downgrade() -> None:
    """Remove hydrated data from the tables."""

    # Clear data from transmissions_with_forecasts for the last 3 days
    op.execute(
        """
        ALTER TABLE transmissions_with_forecasts 
        DELETE WHERE CaptureDateTimeUTC >= now() - INTERVAL 3 DAY
    """
    )

    # Clear data from best_known_forecasts for the last 3 days
    op.execute(
        """
        ALTER TABLE best_known_forecasts 
        DELETE WHERE ForecastDateTimeUTC >= now() - INTERVAL 3 DAY
    """
    )


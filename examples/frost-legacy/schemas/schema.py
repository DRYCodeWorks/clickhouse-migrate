"""
Base schema module for ClickHouse migrations.

This module contains the SQLAlchemy base class and metadata setup.
Define your ClickHouse table models here or import them from other modules.

For ClickHouse-specific features, you can use clickhouse-sqlalchemy types
and features. See: https://github.com/cloudflare/clickhouse-sqlalchemy
"""

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Float32
from sqlalchemy.sql import func

# Create the base class for declarative models
Base = declarative_base()
metadata = Base.metadata

# Configure naming conventions for better consistency
metadata.naming_convention = {
    "ix": "%(column_0_label)s_ix",
    "uq": "uq_%(table_name)s_%(column_0_name)s", 
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Example table definitions - uncomment and modify as needed for your project

# Example 1: Simple events table for time-series data
# class Events(Base):
#     __tablename__ = 'events'
#     
#     id = Column(Integer, primary_key=True)
#     timestamp = Column(DateTime, nullable=False, default=func.now())
#     event_type = Column(String(50), nullable=False)
#     value = Column(Float32)
#     metadata_json = Column(String)  # JSON string for flexible metadata

# Example 2: User analytics table
# class UserActivity(Base):
#     __tablename__ = 'user_activity'
#     
#     id = Column(Integer, primary_key=True)
#     user_id = Column(Integer, nullable=False)
#     action = Column(String(100), nullable=False)
#     timestamp = Column(DateTime, nullable=False, default=func.now())
#     properties = Column(String)  # JSON properties

# Example 3: IoT sensor readings
# class SensorReadings(Base):
#     __tablename__ = 'sensor_readings'
#     
#     id = Column(Integer, primary_key=True)
#     device_id = Column(String(50), nullable=False)
#     sensor_type = Column(String(50), nullable=False)
#     value = Column(Float32, nullable=False)
#     timestamp = Column(DateTime, nullable=False)
#     location_lat = Column(Float32)
#     location_lon = Column(Float32)

# Add your own table definitions below this line
# ...
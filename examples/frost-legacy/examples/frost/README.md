# Frost Weather Monitoring System - Migration Example

This directory contains the original Frost-specific implementation that this ClickHouse migration tool was built for. It serves as a comprehensive example of how to use the tool for a real-world production system.

## About Frost

Frost is a weather monitoring and agricultural technology company that uses IoT devices to collect environmental data. Their system includes:

- **Weather monitoring devices** deployed in agricultural areas
- **Real-time data collection** from sensors (temperature, humidity, soil moisture, etc.) 
- **Computer vision analysis** for weather pattern detection
- **Storm tracking system** for agricultural risk management
- **Data analytics platform** for farmers and researchers

## Architecture Overview

The Frost system uses a hybrid database architecture:

- **SQL Server** - Primary transactional database for device management, user accounts, alerts, and configuration
- **ClickHouse** - Analytics database for time-series sensor data, images, and computed metrics

## Key Components

### Database Schemas

- **Device Management**: Tables for tracking weather stations, their locations, and configurations
- **Sensor Data**: Time-series tables for environmental measurements  
- **Storm Events**: Complex system for tracking weather events at device level
- **Computer Vision**: Image processing and analysis results
- **User Management**: Authentication, permissions, and group management

### ClickHouse Tables

- **Transmissions**: Raw sensor data from devices
- **Images**: Camera captures with metadata
- **Forecasts**: Weather prediction data
- **Materialized Views**: Optimized aggregations for reporting
- **Dictionaries**: Real-time device metadata from API

### Migration Patterns

The Frost implementation demonstrates several advanced patterns:

1. **Multi-Database Coordination**: Managing related schemas across SQL Server and ClickHouse
2. **AWS Integration**: Using Secrets Manager and SSM for credential management
3. **Dynamic Configuration**: Environment-specific API endpoints and roles
4. **Data Pipeline Management**: Complex ETL processes with materialized views
5. **Permission Management**: Fine-grained database role assignments

## Files Structure

```
frost/
├── schemas/           # SQL Server table definitions
│   ├── schema.py     # Main SQLAlchemy models
│   ├── sql/          # Stored procedures and functions
│   └── clickhouse_sql/ # ClickHouse DDL scripts
├── migrations/       # SQL Server migrations
├── clickhouse_migrations/ # ClickHouse migrations  
├── alembic.ini      # Original configuration with Frost environments
├── env.py           # Original AWS-integrated environment setup
└── README.md        # This file
```

## Learning from This Example

This implementation shows how to:

- **Manage multiple database environments** (local, dev, staging, prod)
- **Handle complex credential systems** (AWS Secrets Manager integration)
- **Organize large-scale migrations** (100+ migration files)
- **Implement business-specific patterns** (storm events, device management)
- **Coordinate schema changes** between different database systems

## Adapting for Your Project

To adapt this pattern for your own project:

1. **Study the schema organization** in `schemas/schema.py`
2. **Review migration patterns** in the migration directories
3. **Understand the credential management** in the original `env.py`
4. **Examine ClickHouse optimization techniques** in the SQL files
5. **Note the multi-environment configuration** in `alembic.ini`

The generalized version of this tool abstracts away Frost-specific details while preserving all the sophisticated functionality demonstrated here.

---

*This example represents a production system serving agricultural customers across multiple regions. It demonstrates the tool's capability to handle enterprise-scale database management with complex requirements.*
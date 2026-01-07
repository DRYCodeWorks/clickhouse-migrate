# Storm Events Usage Guide

This guide explains how to use the device-level storm events system for developers and analysts.

## Overview

Storm events in Frost are **device-level** events where each device independently experiences and manages its own storms. Each storm follows a defined lifecycle with rich metadata tracking.

## Storm Lifecycle

```
Predicted (1) ──┬──→ Active (2) ────→ Completed (3)
                └──→ Cancelled (4)
```

### Status Definitions

- **Predicted (1)**: Storm is forecasted but hasn't started yet
- **Active (2)**: Storm conditions are currently occurring at the device
- **Completed (3)**: Storm has ended with clear conditions observed
- **Cancelled (4)**: Predicted storm did not materialize

## Database Schema

### Core Tables

#### StormEvents
Primary storm event table with 1-to-1 device relationship:
```sql
- ID (BIGINT IDENTITY) - Primary key
- DeviceID (BIGINT) - FK to Devices.ID
- StormTypeID (SMALLINT) - FK to StormType (1=Winter, 2=Mixed, 3=Rain)
- StormStatusID (SMALLINT) - FK to StormStatus (1=Predicted, 2=Active, 3=Completed, 4=Cancelled)
- TriggerSource (VARCHAR(50)) - What triggered the storm (CV, Forecast, Sensor, Manual)
- TriggerMetadata (NVARCHAR(MAX)) - JSON metadata referencing ClickHouse data
- StartDateTimeUTC (DATETIME2(3)) - Storm start time
- EndDateTimeUTC (DATETIME2(3)) - Storm end time (set when completed)
- DefinitionTypeID (SMALLINT) - How defined (1=UserDefined, 2=AutoDetected, 3=Retroactive)
- Notes (NVARCHAR(MAX)) - Optional notes
- Standard audit fields (IsActive, Created/Modified dates and users)
```

### Enum Tables
- **StormType**: Winter, Mixed, Rain
- **StormStatus**: Predicted, Active, Completed, Cancelled  
- **StormDefinitionType**: UserDefined, AutoDetected, Retroactive

## Stored Procedures

### sp_CreateStormEvent_v1
Creates a new storm event for a device.

```sql
EXEC sp_CreateStormEvent_v1
    @DeviceID = '65428C0C-C81B-4EBD-9D39-CAEDF5463DA4',
    @StormTypeID = 1,  -- Winter
    @TriggerSource = 'CV',
    @TriggerMetadata = '{"triggers":[{"source":"cv","data":{"snowingConfidence":0.85}}]}',
    @StartDateTimeUTC = '2025-01-15 14:00:00',
    @DefinitionTypeID = 2,  -- AutoDetected
    @CreatedByUserID = NULL,
    @Notes = 'Storm detected by computer vision';
```

**Returns**: StormEventID of created storm

### sp_UpdateStormStatus_v1
Updates storm status with progression validation.

```sql
EXEC sp_UpdateStormStatus_v1
    @StormEventID = 12345,
    @NewStatusID = 2,  -- Active
    @EndDateTimeUTC = NULL,  -- Only set when completing
    @ModifiedByUserID = NULL,
    @Notes = 'Storm conditions confirmed active';
```

**Valid Progressions**:
- Predicted → Active
- Active → Completed  
- Predicted → Cancelled

### sp_CreateRetroactiveStormEvents_v1
Creates a retroactive storm event for a single device.

```sql
EXEC sp_CreateRetroactiveStormEvents_v1
    @DeviceID = 123456,  -- Device ID (BIGINT)
    @StormTypeID = 1,  -- Winter
    @StartDateTimeUTC = '2025-01-15 14:00:00',
    @EndDateTimeUTC = '2025-01-15 18:00:00',
    @TriggerMetadata = '{"triggers":[{"source":"retroactive","data":{"analysisType":"historical"}}]}',
    @CreatedByUserID = NULL,
    @Notes = 'Historical storm identified from analysis';
```

**Returns**: StormEventID of created storm (always marked as Completed)

## TriggerMetadata JSON Structure

### Computer Vision Trigger
```json
{
  "triggers": [
    {
      "source": "cv",
      "timestamp": "2025-01-15T14:30:00Z",
      "data": {
        "table": "images",
        "captureDateTimeUTC": "2025-01-15T14:30:00Z",
        "snowingConfidence": 0.85,
        "snowOnRoadConfidence": 0.72
      }
    }
  ]
}
```

### Forecast Trigger  
```json
{
  "triggers": [
    {
      "source": "forecast",
      "timestamp": "2025-01-15T12:00:00Z", 
      "data": {
        "table": "forecasts",
        "forecastDateTimeUTC": "2025-01-15T14:00:00Z",
        "captureDateTimeUTC": "2025-01-15T12:00:00Z",
        "probabilitySnow": 0.90
      }
    }
  ]
}
```

### Sensor Trigger
```json
{
  "triggers": [
    {
      "source": "sensor",
      "timestamp": "2025-01-15T14:00:00Z",
      "data": {
        "table": "transmissions",
        "captureDateTimeUTC": "2025-01-15T14:00:00Z",
        "surfaceTempC": -2.5,
        "ambientTempC": -5.0
      }
    }
  ]
}
```

## Common Queries

### Get Active Storms for Device
```sql
SELECT se.*, st.Name as StormType, ss.Name as Status
FROM StormEvents se
JOIN StormType st ON se.StormTypeID = st.ID
JOIN StormStatus ss ON se.StormStatusID = ss.ID
WHERE se.DeviceID = @DeviceID 
  AND se.StormStatusID IN (1, 2)  -- Predicted or Active
ORDER BY se.StartDateTimeUTC DESC;
```

### Get Storm History for Device
```sql
SELECT 
    se.ID,
    st.Name as StormType,
    ss.Name as Status,
    se.StartDateTimeUTC,
    se.EndDateTimeUTC,
    DATEDIFF(HOUR, se.StartDateTimeUTC, se.EndDateTimeUTC) as DurationHours,
    se.TriggerSource
FROM StormEvents se
JOIN StormType st ON se.StormTypeID = st.ID  
JOIN StormStatus ss ON se.StormStatusID = ss.ID
WHERE se.DeviceID = @DeviceID
ORDER BY se.StartDateTimeUTC DESC;
```

### Get Current Storm Activity (All Devices)
```sql
SELECT 
    d.Name as DeviceName,
    se.ID as StormID,
    st.Name as StormType,
    ss.Name as Status,
    se.StartDateTimeUTC,
    se.TriggerSource
FROM StormEvents se
JOIN Devices d ON se.DeviceID = d.ID
JOIN StormType st ON se.StormTypeID = st.ID
JOIN StormStatus ss ON se.StormStatusID = ss.ID
WHERE se.StormStatusID IN (1, 2)  -- Predicted or Active
ORDER BY se.StartDateTimeUTC DESC;
```

## Python Integration (SQLAlchemy)

```python
from schemas.schema import StormEvents, StormType, StormStatus, Devices

# Query active storms
active_storms = session.query(StormEvents)\
    .join(StormStatus)\
    .filter(StormStatus.Name.in_(['Predicted', 'Active']))\
    .all()

# Get storm with relationships
storm = session.query(StormEvents)\
    .options(
        joinedload(StormEvents.Device),
        joinedload(StormEvents.StormType),
        joinedload(StormEvents.StormStatus)
    )\
    .filter(StormEvents.ID == storm_id)\
    .first()
```

## Best Practices

### Creating Storms
1. Always validate device existence before creating storms
2. Use appropriate TriggerSource and include relevant metadata
3. Set realistic StartDateTimeUTC (not far in future for Predicted storms)
4. Include meaningful Notes for manual storms

### Status Updates
1. Follow valid progression rules (no backwards progression)
2. Always set EndDateTimeUTC when marking Completed
3. Include contextual Notes explaining status changes
4. Use ModifiedByUserID for audit trails

### TriggerMetadata
1. Always include timestamp and source
2. Reference actual ClickHouse table/timestamp when possible
3. Keep JSON structure consistent across trigger types
4. Include confidence scores for CV triggers

### Querying
1. Use proper indexes (DeviceID, dates, status)
2. Join with enum tables for human-readable names
3. Filter by IsActive = 1 for current data
4. Use date ranges for performance on large datasets

## Error Handling

Common error scenarios:
- **Invalid Device ID**: Procedure will raise error if device doesn't exist
- **Invalid Status Progression**: Status update will fail with constraint error  
- **Missing Required Fields**: NULL constraints will prevent invalid data
- **Foreign Key Violations**: Invalid enum IDs will be rejected

## Testing

See `tests/storm_events/` directory for comprehensive test scripts:
- `test_create_storm.sql` - Storm creation scenarios
- `test_update_status.sql` - Status progression testing
- `test_validation.sql` - Data integrity queries
- `test_error_cases.sql` - Error handling validation
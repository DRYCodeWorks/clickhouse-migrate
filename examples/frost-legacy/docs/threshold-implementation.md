# Storm Threshold Implementation

## Overview

The storm threshold system allows Frost to define configurable rules for storm start and end conditions. It supports both system-wide defaults and device-specific overrides, providing granular control for individual device locations.

## Architecture

### Core Components

1. **StormThresholds Table**: Stores threshold rules as JSON
2. **StartThresholdSnapshot & EndThresholdSnapshot**: Immutable audit trail in StormEvents
3. **fn_GetStormThresholds**: Helper function for inheritance logic
4. **sp_CreateStormEvent_v2**: Creates storm with start threshold tracking
5. **sp_CompleteStormEvent_v1**: Completes storm with end threshold tracking
6. **sp_UpsertDeviceThreshold**: Management interface for device overrides

### Design Principles

- **Inheritance Model**: Devices use Frost defaults unless explicitly overridden
- **JSON Flexibility**: Rules stored as JSON for easy evolution without schema changes
- **Immutable Audit Trail**: Each storm preserves the exact thresholds used at creation time
- **User Accountability**: All threshold changes tracked with user and timestamp

## Database Schema

### StormThresholds Table

```sql
CREATE TABLE StormThresholds (
    ID INT IDENTITY(1,1) PRIMARY KEY,
    DeviceID BIGINT NULL,                       -- NULL = Frost defaults
    StormTypeID SMALLINT NOT NULL,              -- FK to StormType
    StartRules JSON NULL,                       -- Native JSON with start conditions
    EndRules JSON NULL,                         -- Native JSON with end conditions
    IsActive BIT NOT NULL DEFAULT 1,
    CreatedDateTimeUTC DATETIME2(3) NOT NULL DEFAULT GETUTCDATE(),
    CreatedUserID UNIQUEIDENTIFIER NULL,        -- FK to Users
    ModifiedDateTimeUTC DATETIME2(3) NULL,
    ModifiedUserID UNIQUEIDENTIFIER NULL,       -- FK to Users
    
    CONSTRAINT FK_StormThresholds_DeviceID FOREIGN KEY (DeviceID) REFERENCES Devices(ID),
    CONSTRAINT FK_StormThresholds_StormTypeID FOREIGN KEY (StormTypeID) REFERENCES StormType(ID),
    CONSTRAINT UQ_StormThresholds_DeviceID_StormTypeID UNIQUE (DeviceID, StormTypeID)
);
```

### StormEvents Enhancement

```sql
ALTER TABLE StormEvents
ADD StartThresholdSnapshot JSON NULL,
    EndThresholdSnapshot JSON NULL;
```

## JSON Schema Structure

### Example Start Rules Structure (TBD)
```json
{
  "temp_below_f": "<threshold>",
  "cv_snowing_confidence_min": "<threshold>",
  "cv_snow_on_road_confidence_min": "<threshold>",
  "forecast_snow_prob_min": "<threshold>",
  "forecast_hours_ahead": "<hours>",
  "precip_rate_min_in_hr": "<rate>",
  "rule_logic": "<AND|OR|COMPLEX>",
  "description": "<human-readable description>"
}
```

### Example End Rules Structure (TBD)
```json
{
  "hours_no_precip": "<hours>",
  "temp_above_f": "<threshold>",
  "cv_clear_pavement_confidence_min": "<threshold>",
  "hours_above_freezing": "<hours>",
  "rule_logic": "<AND|OR|COMPLEX>",
  "description": "<human-readable description>"
}
```

**Note**: Specific threshold values and rule logic will be defined once the rules engine is implemented.

### Start Threshold Snapshot Structure
```json
{
  "rules": {
    /* Copy of StartRules from StormThresholds at time of storm start */
  },
  "source": "device | default",
  "device_id": "<device_id or null>",
  "threshold_id": "<threshold_record_id>",
  "captured_at": "<ISO 8601 timestamp>"
}
```

### End Threshold Snapshot Structure
```json
{
  "rules": {
    /* Copy of EndRules from StormThresholds at time of storm end */
  },
  "source": "device | default",
  "device_id": "<device_id or null>",
  "threshold_id": "<threshold_record_id>",
  "captured_at": "<ISO 8601 timestamp>"
}
```

## API Usage Patterns

### Getting Effective Thresholds
```sql
-- Get effective thresholds for a device (returns table)
SELECT 
    StartRules,
    EndRules, 
    Source,
    DeviceID,
    ThresholdID,
    JSON_VALUE(StartRules, '$.temp_below_f') AS TempThreshold,
    JSON_VALUE(EndRules, '$.hours_no_precip') AS EndHours
FROM dbo.fn_GetStormThresholds_v1(@DeviceID, 1); -- Winter storm
```

### Creating Storm with Thresholds
```sql
-- Create predicted storm (default behavior)
EXEC sp_CreateStormEvent_v2
    @DeviceID = 12345,
    @StormTypeID = 1,
    @TriggerSource = 'Forecast',
    @TriggerMetadata = '{"confidence": 0.75, "hours_ahead": 6}';
    -- StormStatusID defaults to 1 (Predicted)
    -- ThresholdSnapshot will be auto-populated

-- Create active storm (real-time CV detection)
EXEC sp_CreateStormEvent_v2
    @DeviceID = 12345,
    @StormTypeID = 1,
    @StormStatusID = 2, -- Active
    @TriggerSource = 'CV',
    @TriggerMetadata = '{"confidence": 0.85, "detection_type": "snow"}';

-- Create completed storm (retroactive analysis)
EXEC sp_CreateStormEvent_v2
    @DeviceID = 12345,
    @StormTypeID = 1,
    @StormStatusID = 3, -- Completed
    @StartDateTimeUTC = '2025-08-10 08:00:00',
    @TriggerSource = 'Retroactive',
    @DefinitionTypeID = 3; -- Retroactive
```

### Setting Device Override
```sql
-- Set complete device override
EXEC sp_UpsertDeviceThreshold_v1
    @DeviceID = 12345,
    @StormTypeID = 1,
    @StartRules = '{"temp_below_f": 32, "cv_confidence_min": 0.8}',
    @EndRules = '{"hours_no_precip": 4, "temp_above_f": 45}',
    @UserID = '87654321-4321-4321-4321-210987654321',
    @Notes = 'Stricter thresholds for highway location device';

-- Set partial override (missing rules will use defaults)
EXEC sp_UpsertDeviceThreshold_v1
    @DeviceID = 12345,
    @StormTypeID = 1,
    @StartRules = '{"temp_below_f": 30}', -- Only override start rules
    @EndRules = NULL, -- Will use default end rules
    @UserID = '87654321-4321-4321-4321-210987654321',
    @Notes = 'Only customize start temperature for this device';
```

## Implementation Steps

### Phase 1: Database Updates
1. Apply schema changes via Alembic migration
2. Deploy new functions and stored procedures
3. Verify JSON constraints are working

### Phase 2: Default Population
```sql
-- Default thresholds will be inserted once the rules engine is implemented
-- INSERT INTO StormThresholds (DeviceID, StormTypeID, StartRules, EndRules, CreatedUserID) 
-- VALUES (NULL, <storm_type>, <start_rules_json>, <end_rules_json>, NULL);
```

**Note**: Default threshold values are pending implementation of the rules engine that will process them.

### Phase 3: Service Integration
1. Update storm creation services to use v2 procedures
2. Build admin interface for threshold management
3. Implement monitoring for threshold effectiveness

## Benefits

1. **Native JSON Support**: SQL Server 2016+ native JSON type with automatic validation
2. **Flexibility**: JSON rules can evolve without schema changes
3. **Accountability**: Full audit trail of who changed what and when
4. **Granularity**: Device-level control for location-specific conditions
5. **Traceability**: Each storm preserves exact thresholds used for creation
6. **Customization**: Each device can have unique thresholds based on its environment
7. **Performance**: Native JSON indexing and querying capabilities
8. **Simplified Logic**: Direct device lookup without group inheritance chain
9. **Table-Valued Function**: Returns structured data that's easy to JOIN and query

## Future Enhancements

1. **Complex Rules**: Support for AND/OR logic, ranges, and conditions
2. **Seasonal Adjustments**: Time-based threshold variations
3. **ML Integration**: Adaptive thresholds based on performance data
4. **Validation**: Schema validation for JSON rule structures
5. **Templates**: Pre-defined threshold sets for common scenarios

## Migration Notes

- Version 2 procedures are backward compatible
- Existing storms will have NULL ThresholdSnapshot (expected)
- Default thresholds should be defined by the team before production deployment
- Consider gradual rollout with monitoring of threshold effectiveness
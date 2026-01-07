/*
================================================================================
Stored Procedure: sp_CreateStormEvent_v2
Description: Creates a storm event for a single device with threshold snapshot
             Version 2 adds threshold tracking for audit trail
             
Parameters:
    @DeviceID - ID of the device experiencing the storm
    @StormTypeID - Type of storm (1=Winter, 2=Mixed, 3=Rain)
    @StormStatusID - Initial status (1=Predicted, 2=Active, 3=Completed, defaults to Predicted)
    @TriggerSource - Source system triggering the storm (CV, Sensor, Forecast, etc.)
    @TriggerMetadata - JSON metadata about the triggering data
    @StartThresholdSnapshot - JSON snapshot of start thresholds used (optional, will auto-fetch)
    @StartDateTimeUTC - When the storm started (defaults to current time)
    @DefinitionTypeID - How storm was defined (1=User, 2=Auto, 3=Retroactive)
    @CreatedByUserID - User creating the storm (can be NULL for system-generated)
    @Notes - Optional notes about the storm
    
Version: 2
Date: 2025-08-14
================================================================================
*/

CREATE PROCEDURE sp_CreateStormEvent_v2
    @DeviceID BIGINT,
    @StormTypeID SMALLINT,
    @StormStatusID SMALLINT = 1, -- Default to Predicted
    @TriggerSource NVARCHAR(50) = NULL,
    @TriggerMetadata NVARCHAR(MAX) = NULL,
    @StartThresholdSnapshot NVARCHAR(MAX) = NULL,  -- NEW: Start threshold snapshot
    @StartDateTimeUTC DATETIME2(3) = NULL,
    @DefinitionTypeID SMALLINT = 2, -- Default to AutoDetected
    @CreatedByUserID UNIQUEIDENTIFIER = NULL,
    @Notes NVARCHAR(MAX) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Constants
    DECLARE @Now DATETIME2(3) = GETUTCDATE();
    
    -- Working variables
    DECLARE @StormEventID BIGINT;
    DECLARE @StartTime DATETIME2(3) = ISNULL(@StartDateTimeUTC, @Now);
    
    -- Validate device exists
    IF NOT EXISTS (SELECT 1 FROM Devices WHERE ID = @DeviceID)
    BEGIN
        RAISERROR('Device ID %I64d does not exist', 16, 1, @DeviceID);
        RETURN;
    END
    
    -- Validate storm status exists
    IF NOT EXISTS (SELECT 1 FROM StormStatus WHERE ID = @StormStatusID)
    BEGIN
        RAISERROR('Storm status ID %d does not exist', 16, 1, @StormStatusID);
        RETURN;
    END
    
    -- If no start threshold snapshot provided, get current effective thresholds
    IF @StartThresholdSnapshot IS NULL
    BEGIN
        SELECT @StartThresholdSnapshot = (
            SELECT 
                StartRules AS [rules],
                Source AS [source],
                CAST(DeviceID AS NVARCHAR(20)) AS [device_id],
                ThresholdID AS [threshold_id],
                CONVERT(NVARCHAR(30), @Now, 127) AS [captured_at]
            FROM dbo.fn_GetStormThresholds_v1(@DeviceID, @StormTypeID)
            FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
        );
    END
    
    -- StartThresholdSnapshot validation handled by JSON column type
    
    -- Create the storm event
    INSERT INTO StormEvents (
        DeviceID,
        StormTypeID,
        StormStatusID,
        TriggerSource,
        TriggerMetadata,
        StartThresholdSnapshot,
        StartDateTimeUTC,
        DefinitionTypeID,
        CreatedUserID,
        Notes
    )
    VALUES (
        @DeviceID,
        @StormTypeID,
        @StormStatusID,
        @TriggerSource,
        @TriggerMetadata,
        @StartThresholdSnapshot,
        @StartTime,
        @DefinitionTypeID,
        @CreatedByUserID,
        @Notes
    );
    
    -- Capture the generated storm event ID
    SET @StormEventID = SCOPE_IDENTITY();
    
    -- Return the created storm event ID and threshold info
    SELECT 
        @StormEventID AS StormEventID,
        @StartThresholdSnapshot AS StartThresholdSnapshot,
        CASE WHEN @StartThresholdSnapshot IS NOT NULL THEN 1 ELSE 0 END AS HasThresholds;
END;
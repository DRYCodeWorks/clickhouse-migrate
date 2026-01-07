/*
================================================================================
Stored Procedure: sp_CreateStormEvent_v1
Description: Creates a storm event for a single device with trigger metadata
             
Parameters:
    @DeviceID - ID of the device experiencing the storm
    @StormTypeID - Type of storm (1=Winter, 2=Mixed, 3=Rain)
    @TriggerSource - Source system triggering the storm (CV, Sensor, Forecast, etc.)
    @TriggerMetadata - JSON metadata about the triggering data
    @StartDateTimeUTC - When the storm started (defaults to current time)
    @DefinitionTypeID - How storm was defined (1=User, 2=Auto, 3=Retroactive)
    @CreatedByUserID - User creating the storm (can be NULL for system-generated)
    @Notes - Optional notes about the storm
    
Version: 1
Date: 2025-08-13
================================================================================
*/

CREATE PROCEDURE sp_CreateStormEvent_v1
    @DeviceID BIGINT,
    @StormTypeID SMALLINT,
    @TriggerSource NVARCHAR(50) = NULL,
    @TriggerMetadata NVARCHAR(MAX) = NULL,
    @StartDateTimeUTC DATETIME2(3) = NULL,
    @DefinitionTypeID SMALLINT = 2, -- Default to AutoDetected
    @CreatedByUserID UNIQUEIDENTIFIER = NULL,
    @Notes NVARCHAR(MAX) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Constants
    DECLARE @PREDICTED_STATUS_ID SMALLINT = 1;
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
    
    -- Create the storm event
    INSERT INTO StormEvents (
        DeviceID,
        StormTypeID,
        StormStatusID,
        TriggerSource,
        TriggerMetadata,
        StartDateTimeUTC,
        DefinitionTypeID,
        CreatedUserID,
        Notes
    )
    VALUES (
        @DeviceID,
        @StormTypeID,
        @PREDICTED_STATUS_ID,
        @TriggerSource,
        @TriggerMetadata,
        @StartTime,
        @DefinitionTypeID,
        @CreatedByUserID,
        @Notes
    );
    
    -- Capture the generated storm event ID
    SET @StormEventID = SCOPE_IDENTITY();
    
    -- Return the created storm event ID
    SELECT @StormEventID AS StormEventID;
END;
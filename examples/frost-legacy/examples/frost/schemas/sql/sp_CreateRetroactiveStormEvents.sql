/*
================================================================================
Stored Procedure: sp_CreateRetroactiveStormEvents_v1
Description: Creates a retroactive storm event for a single device
             Storm is marked as completed since it occurred in the past
             
Parameters:
    @DeviceID - Device ID for the retroactive storm
    @StormTypeID - Type of storm (1=Winter, 2=Mixed, 3=Rain)
    @StartDateTimeUTC - When the storm started
    @EndDateTimeUTC - When the storm ended  
    @TriggerMetadata - JSON metadata about the triggering data
    @CreatedByUserID - User creating the storm (optional)
    @Notes - Notes about the retroactive storm (optional)
    
Returns:
    StormEventID of the created storm
    
Version: 1
Date: 2025-08-13
================================================================================
*/

CREATE PROCEDURE sp_CreateRetroactiveStormEvents_v1
    @DeviceID BIGINT,
    @StormTypeID SMALLINT,
    @StartDateTimeUTC DATETIME2(3),
    @EndDateTimeUTC DATETIME2(3),
    @TriggerMetadata NVARCHAR(MAX) = NULL,
    @CreatedByUserID UNIQUEIDENTIFIER = NULL,
    @Notes NVARCHAR(MAX) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Constants
    DECLARE @COMPLETED_STATUS_ID SMALLINT = 3;
    DECLARE @RETROACTIVE_DEFINITION_TYPE_ID SMALLINT = 3;
    DECLARE @StormEventID BIGINT;
    
    -- Validate device exists
    IF NOT EXISTS (SELECT 1 FROM Devices WHERE ID = @DeviceID)
    BEGIN
        RAISERROR('Device ID %I64d does not exist', 16, 1, @DeviceID);
        RETURN;
    END
    
    -- Validate date range
    IF @StartDateTimeUTC >= @EndDateTimeUTC
    BEGIN
        RAISERROR('StartDateTimeUTC must be before EndDateTimeUTC', 16, 1);
        RETURN;
    END
    
    -- Create the retroactive storm event
    INSERT INTO StormEvents (
        DeviceID,
        StormTypeID,
        StormStatusID,
        TriggerSource,
        TriggerMetadata,
        StartDateTimeUTC,
        EndDateTimeUTC,
        DefinitionTypeID,
        CreatedUserID,
        Notes
    )
    VALUES (
        @DeviceID,
        @StormTypeID,
        @COMPLETED_STATUS_ID,
        'Retroactive',
        @TriggerMetadata,
        @StartDateTimeUTC,
        @EndDateTimeUTC,
        @RETROACTIVE_DEFINITION_TYPE_ID,
        @CreatedByUserID,
        ISNULL(@Notes, 'Retroactively defined storm event')
    );
    
    -- Capture the generated storm event ID
    SET @StormEventID = SCOPE_IDENTITY();
    
    -- Return the created storm event ID
    SELECT @StormEventID AS StormEventID;
END;
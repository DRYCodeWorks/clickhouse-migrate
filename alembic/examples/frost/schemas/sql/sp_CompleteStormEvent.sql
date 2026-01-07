/*
================================================================================
Stored Procedure: sp_CompleteStormEvent_v1
Description: Completes a storm event and captures the end threshold snapshot
             Used when storm conditions have ended
             
Parameters:
    @StormEventID - ID of the storm event to complete
    @EndDateTimeUTC - When the storm ended (defaults to current time)
    @EndThresholdSnapshot - JSON snapshot of end thresholds used (optional, will auto-fetch)
    @ModifiedByUserID - User completing the storm (can be NULL for system-generated)
    @Notes - Optional notes about storm completion
    
Logic:
    - Validates storm exists and is in Active status
    - Captures end threshold snapshot if not provided
    - Updates storm status to Completed
    - Sets end date and audit fields
    
Version: 1
Date: 2025-08-14
================================================================================
*/

CREATE PROCEDURE sp_CompleteStormEvent_v1
    @StormEventID BIGINT,
    @EndDateTimeUTC DATETIME2(3) = NULL,
    @EndThresholdSnapshot NVARCHAR(MAX) = NULL,
    @ModifiedByUserID UNIQUEIDENTIFIER = NULL,
    @Notes NVARCHAR(MAX) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Constants
    DECLARE @Now DATETIME2(3) = GETUTCDATE();
    DECLARE @CompletedStatusID SMALLINT = 3; -- Completed
    
    -- Working variables
    DECLARE @EndTime DATETIME2(3) = ISNULL(@EndDateTimeUTC, @Now);
    DECLARE @DeviceID BIGINT;
    DECLARE @StormTypeID SMALLINT;
    DECLARE @CurrentStatusID SMALLINT;
    
    -- Get storm event details
    SELECT 
        @DeviceID = DeviceID,
        @StormTypeID = StormTypeID,
        @CurrentStatusID = StormStatusID
    FROM StormEvents
    WHERE ID = @StormEventID;
    
    -- Validate storm event exists
    IF @DeviceID IS NULL
    BEGIN
        RAISERROR('Storm event ID %I64d does not exist', 16, 1, @StormEventID);
        RETURN;
    END
    
    -- Validate storm is in Active status
    IF @CurrentStatusID != 2 -- Active
    BEGIN
        RAISERROR('Storm event %I64d is not in Active status (current status: %d)', 16, 1, @StormEventID, @CurrentStatusID);
        RETURN;
    END
    
    -- If no end threshold snapshot provided, get current effective thresholds
    IF @EndThresholdSnapshot IS NULL
    BEGIN
        SELECT @EndThresholdSnapshot = (
            SELECT 
                EndRules AS [rules],
                Source AS [source],
                CAST(DeviceID AS NVARCHAR(20)) AS [device_id],
                ThresholdID AS [threshold_id],
                CONVERT(NVARCHAR(30), @Now, 127) AS [captured_at]
            FROM dbo.fn_GetStormThresholds_v1(@DeviceID, @StormTypeID)
            FOR JSON PATH, WITHOUT_ARRAY_WRAPPER
        );
    END
    
    -- Update the storm event to completed
    UPDATE StormEvents
    SET StormStatusID = @CompletedStatusID,
        EndDateTimeUTC = @EndTime,
        EndThresholdSnapshot = @EndThresholdSnapshot,
        ModifiedDateTimeUTC = @Now,
        ModifiedUserID = @ModifiedByUserID,
        Notes = CASE 
            WHEN @Notes IS NOT NULL 
            THEN ISNULL(Notes + CHAR(13) + CHAR(10), '') + @Notes 
            ELSE Notes 
        END
    WHERE ID = @StormEventID;
    
    -- Return the completed storm event info
    SELECT 
        @StormEventID AS StormEventID,
        @CompletedStatusID AS NewStatusID,
        @EndTime AS EndDateTimeUTC,
        @EndThresholdSnapshot AS EndThresholdSnapshot,
        'Completed' AS Action;
END;
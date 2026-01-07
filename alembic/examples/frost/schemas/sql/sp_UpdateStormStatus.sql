/*
================================================================================
Stored Procedure: sp_UpdateStormStatus_v1
Description: Updates storm event status and optionally ends the storm
             Supports status progression: Predicted → Active → Completed
             
Parameters:
    @StormEventID - ID of the storm event to update
    @NewStatusID - New status (1=Predicted, 2=Active, 3=Completed, 4=Cancelled)
    @EndDateTimeUTC - When to end the storm (optional, defaults to current time for Completed/Cancelled)
    @TriggerMetadata - Additional trigger metadata to append (optional)
    @ModifiedByUserID - User making the change (optional)
    @Notes - Additional notes to append (optional)
    
Logic:
    - Only allows forward progression in status (no going backwards)
    - Automatically sets EndDateTimeUTC when status becomes Completed or Cancelled
    - Can append additional trigger metadata to existing metadata
    
Version: 1
Date: 2025-08-13
================================================================================
*/

CREATE PROCEDURE sp_UpdateStormStatus_v1
    @StormEventID BIGINT,
    @NewStatusID SMALLINT,
    @EndDateTimeUTC DATETIME2(3) = NULL,
    @TriggerMetadata NVARCHAR(MAX) = NULL,
    @ModifiedByUserID UNIQUEIDENTIFIER = NULL,
    @Notes NVARCHAR(MAX) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    -- Variables
    DECLARE @CurrentStatusID SMALLINT;
    DECLARE @CurrentMetadata NVARCHAR(MAX);
    DECLARE @CurrentNotes NVARCHAR(MAX);
    DECLARE @UpdatedMetadata NVARCHAR(MAX);
    DECLARE @UpdatedNotes NVARCHAR(MAX);
    DECLARE @Now DATETIME2(3) = GETUTCDATE();
    DECLARE @FinalEndTime DATETIME2(3);
    
    -- Get current storm state
    SELECT 
        @CurrentStatusID = StormStatusID,
        @CurrentMetadata = TriggerMetadata,
        @CurrentNotes = Notes
    FROM StormEvents
    WHERE ID = @StormEventID;
    
    -- Validate storm exists
    IF @CurrentStatusID IS NULL
    BEGIN
        RAISERROR('Storm event ID %I64d does not exist', 16, 1, @StormEventID);
        RETURN;
    END
    
    -- Validate status progression (no going backwards)
    IF @NewStatusID < @CurrentStatusID
    BEGIN
        RAISERROR('Cannot move storm status backwards from %d to %d', 16, 1, @CurrentStatusID, @NewStatusID);
        RETURN;
    END
    
    -- Handle metadata merging if new metadata provided
    SET @UpdatedMetadata = @CurrentMetadata;
    IF @TriggerMetadata IS NOT NULL
    BEGIN
        IF @CurrentMetadata IS NULL
            SET @UpdatedMetadata = @TriggerMetadata;
        ELSE
        BEGIN
            -- Simple append for now - could implement JSON merging later
            SET @UpdatedMetadata = @CurrentMetadata + CHAR(13) + CHAR(10) + '--- Additional Trigger ---' + CHAR(13) + CHAR(10) + @TriggerMetadata;
        END
    END
    
    -- Handle notes merging if new notes provided
    SET @UpdatedNotes = @CurrentNotes;
    IF @Notes IS NOT NULL
    BEGIN
        IF @CurrentNotes IS NULL
            SET @UpdatedNotes = @Notes;
        ELSE
            SET @UpdatedNotes = @CurrentNotes + CHAR(13) + CHAR(10) + @Notes;
    END
    
    -- Determine end time
    SET @FinalEndTime = @EndDateTimeUTC;
    IF @FinalEndTime IS NULL AND @NewStatusID IN (3, 4) -- Completed or Cancelled
        SET @FinalEndTime = @Now;
    
    -- Update the storm event
    UPDATE StormEvents
    SET 
        StormStatusID = @NewStatusID,
        EndDateTimeUTC = @FinalEndTime,
        TriggerMetadata = @UpdatedMetadata,
        Notes = @UpdatedNotes,
        ModifiedDateTimeUTC = @Now,
        ModifiedUserID = @ModifiedByUserID
    WHERE ID = @StormEventID;
    
    -- Return success
    SELECT @StormEventID AS StormEventID, @NewStatusID AS NewStatusID;
END;
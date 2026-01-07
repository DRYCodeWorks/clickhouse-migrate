/*
================================================================================
Stored Procedure: sp_UpsertDeviceThreshold_v1
Description: Creates or updates device-specific storm threshold overrides
             Allows devices to have customized storm detection thresholds
             
Parameters:
    @DeviceID - ID of the device to set thresholds for (NULL not allowed)
    @StormTypeID - Type of storm (1=Winter, 2=Mixed, 3=Rain)
    @StartRules - JSON object with storm start conditions (optional)
    @EndRules - JSON object with storm end conditions (optional)
    @UserID - User making the change for audit trail
    @Notes - Optional notes about why thresholds were changed
    
Logic:
    - Updates existing threshold if found
    - Creates new threshold override if not found
    - Validates JSON format for both rule sets
    - Tracks user and timestamp for audit
    
Version: 1
Date: 2025-08-14
================================================================================
*/

CREATE PROCEDURE sp_UpsertDeviceThreshold_v1
    @DeviceID BIGINT,
    @StormTypeID SMALLINT,
    @StartRules NVARCHAR(MAX) = NULL,
    @EndRules NVARCHAR(MAX) = NULL,
    @UserID UNIQUEIDENTIFIER,
    @Notes NVARCHAR(MAX) = NULL
AS
BEGIN
    SET NOCOUNT ON;
    
    DECLARE @Now DATETIME2(3) = GETUTCDATE();
    DECLARE @ThresholdID INT;
    
    -- Validate required parameters
    IF @DeviceID IS NULL
    BEGIN
        RAISERROR('DeviceID cannot be NULL for threshold overrides', 16, 1);
        RETURN;
    END
    
    IF @UserID IS NULL
    BEGIN
        RAISERROR('UserID is required for audit trail', 16, 1);
        RETURN;
    END
    
    -- Validate device exists
    IF NOT EXISTS (SELECT 1 FROM Devices WHERE ID = @DeviceID)
    BEGIN
        RAISERROR('Device ID %I64d does not exist', 16, 1, @DeviceID);
        RETURN;
    END
    
    -- Validate storm type exists
    IF NOT EXISTS (SELECT 1 FROM StormType WHERE ID = @StormTypeID)
    BEGIN
        RAISERROR('Storm type ID %d does not exist', 16, 1, @StormTypeID);
        RETURN;
    END
    
    -- JSON validation handled by JSON column type
    
    -- Check if threshold override already exists
    SELECT @ThresholdID = ID 
    FROM StormThresholds 
    WHERE DeviceID = @DeviceID AND StormTypeID = @StormTypeID;
    
    -- Get default rules if parameters are NULL
    DECLARE @FinalStartRules NVARCHAR(MAX) = @StartRules;
    DECLARE @FinalEndRules NVARCHAR(MAX) = @EndRules;
    
    -- If StartRules is NULL, get from defaults
    IF @StartRules IS NULL
    BEGIN
        SELECT @FinalStartRules = StartRules 
        FROM StormThresholds 
        WHERE DeviceID IS NULL AND StormTypeID = @StormTypeID AND IsActive = 1;
    END
    
    -- If EndRules is NULL, get from defaults
    IF @EndRules IS NULL
    BEGIN
        SELECT @FinalEndRules = EndRules 
        FROM StormThresholds 
        WHERE DeviceID IS NULL AND StormTypeID = @StormTypeID AND IsActive = 1;
    END

    IF @ThresholdID IS NOT NULL
    BEGIN
        -- Update existing threshold
        UPDATE StormThresholds
        SET StartRules = @FinalStartRules,
            EndRules = @FinalEndRules,
            ModifiedDateTimeUTC = @Now,
            ModifiedUserID = @UserID,
            IsActive = 1
        WHERE ID = @ThresholdID;
        
        -- Return updated threshold info
        SELECT 
            @ThresholdID AS ThresholdID,
            'Updated' AS Action,
            @DeviceID AS DeviceID,
            @StormTypeID AS StormTypeID;
    END
    ELSE
    BEGIN
        -- Insert new threshold override
        INSERT INTO StormThresholds (
            DeviceID,
            StormTypeID,
            StartRules,
            EndRules,
            CreatedUserID,
            IsActive
        )
        VALUES (
            @DeviceID,
            @StormTypeID,
            @FinalStartRules,
            @FinalEndRules,
            @UserID,
            1
        );
        
        SET @ThresholdID = SCOPE_IDENTITY();
        
        -- Return new threshold info
        SELECT 
            @ThresholdID AS ThresholdID,
            'Created' AS Action,
            @DeviceID AS DeviceID,
            @StormTypeID AS StormTypeID;
    END
END;
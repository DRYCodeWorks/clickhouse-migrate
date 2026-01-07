/*
================================================================================
Function: fn_GetStormThresholds_v1
Description: Gets effective storm thresholds for a device and storm type
             Returns device-specific thresholds if they exist, otherwise defaults
             
Parameters:
    @DeviceID - ID of the device to get thresholds for
    @StormTypeID - Type of storm (1=Winter, 2=Mixed, 3=Rain)
    
Returns:
    Table with columns:
    - StartRules: JSON with storm start conditions
    - EndRules: JSON with storm end conditions  
    - Source: 'device' if device-specific, 'default' if using Frost defaults
    - DeviceID: ID of the device (NULL for defaults)
    - ThresholdID: ID of the threshold record used
    
Version: 1
Date: 2025-08-14
================================================================================
*/

CREATE FUNCTION fn_GetStormThresholds_v1(
    @DeviceID BIGINT, 
    @StormTypeID SMALLINT
)
RETURNS TABLE
AS
RETURN (
    SELECT TOP 1
        StartRules,
        EndRules,
        CASE WHEN st.DeviceID IS NULL THEN 'default' ELSE 'device' END AS Source,
        st.DeviceID,
        st.ID AS ThresholdID
    FROM StormThresholds st
    WHERE (st.DeviceID = @DeviceID OR st.DeviceID IS NULL)
        AND st.StormTypeID = @StormTypeID
        AND st.IsActive = 1
    ORDER BY st.DeviceID DESC  -- Non-NULL (device override) comes before NULL (default)
);
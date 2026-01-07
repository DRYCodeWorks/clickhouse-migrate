DECLARE @spid INT = 149;
SELECT percent_complete, estimated_completion_time / (1000.0 * 60 * 60) AS estimated_completion_time_hours
  FROM sys.dm_exec_requests
  WHERE session_id = @spid;

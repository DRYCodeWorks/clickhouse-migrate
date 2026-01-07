USE [frost-db-prd];

-- Select on Tables
REVOKE SELECT ON [dbo].[SnowDepthCalibrationRequests] TO [frost_api_role];
REVOKE SELECT ON [dbo].[SnowDepthCalibrationRequests] TO [frost_particle_role];


-- Insert on Tables
REVOKE INSERT ON [dbo].[SnowDepthCalibrationRequests] TO [frost_api_role];
REVOKE INSERT ON [dbo].[SnowDepthCalibrationRequests] TO [frost_particle_role];
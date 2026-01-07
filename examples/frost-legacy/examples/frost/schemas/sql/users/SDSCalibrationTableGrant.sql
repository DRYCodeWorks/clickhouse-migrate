USE [frost-db-prd];

-- Select on Tables
GRANT SELECT ON [dbo].[SnowDepthCalibrationRequests] TO [frost_api_role];
GRANT SELECT ON [dbo].[SnowDepthCalibrationRequests] TO [frost_particle_role];


-- Insert on Tables
GRANT INSERT ON [dbo].[SnowDepthCalibrationRequests] TO [frost_api_role];
GRANT INSERT ON [dbo].[SnowDepthCalibrationRequests] TO [frost_particle_role];
-- Drop tables with proper dependency handling
-- This script will drop views, foreign keys, and tables in the correct order

-- Step 1: Drop views that reference the target tables
PRINT '=== DROPPING DEPENDENT VIEWS ===';

-- Drop vw_DeviceReadings view
IF EXISTS (SELECT * FROM sys.views WHERE name = 'vw_DeviceReadings')
BEGIN
    PRINT 'Dropping view vw_DeviceReadings...';
    DROP VIEW [dbo].[vw_DeviceReadings];
    PRINT 'View vw_DeviceReadings dropped successfully.';
END
ELSE
BEGIN
    PRINT 'View vw_DeviceReadings does not exist.';
END
GO

-- Check for other views that might reference these tables
DECLARE @sql NVARCHAR(MAX) = '';
SELECT @sql = @sql + 'DROP VIEW [' + SCHEMA_NAME(schema_id) + '].[' + name + '];' + CHAR(13)
FROM sys.views v
WHERE OBJECT_DEFINITION(v.object_id) LIKE '%DeviceReadings%'
   OR OBJECT_DEFINITION(v.object_id) LIKE '%DeviceImages%'
   OR OBJECT_DEFINITION(v.object_id) LIKE '%DeviceImageDetails%'
   OR OBJECT_DEFINITION(v.object_id) LIKE '%ComputerVision%'
   OR OBJECT_DEFINITION(v.object_id) LIKE '%SnowDepthReadings%';

IF @sql != ''
BEGIN
    PRINT 'Dropping additional views that reference target tables:';
    PRINT @sql;
    EXEC sp_executesql @sql;
END
ELSE
BEGIN
    PRINT 'No additional views found referencing target tables.';
END
GO

-- Step 2: Drop foreign key constraints
PRINT '=== DROPPING FOREIGN KEY CONSTRAINTS ===';

-- Get and drop all foreign keys referencing target tables
DECLARE @fk_sql NVARCHAR(MAX) = '';
SELECT @fk_sql = @fk_sql + 
    'ALTER TABLE [' + SCHEMA_NAME(fk.schema_id) + '].[' + OBJECT_NAME(fk.parent_object_id) + '] ' +
    'DROP CONSTRAINT [' + fk.name + '];' + CHAR(13)
FROM sys.foreign_keys fk
WHERE OBJECT_NAME(fk.referenced_object_id) IN ('DeviceReadings', 'DeviceImages', 'DeviceImageDetails', 'ComputerVision', 'SnowDepthReadings')
   OR OBJECT_NAME(fk.parent_object_id) IN ('DeviceReadings', 'DeviceImages', 'DeviceImageDetails', 'ComputerVision', 'SnowDepthReadings');

IF @fk_sql != ''
BEGIN
    PRINT 'Dropping foreign key constraints:';
    PRINT @fk_sql;
    EXEC sp_executesql @fk_sql;
    PRINT 'Foreign key constraints dropped successfully.';
END
ELSE
BEGIN
    PRINT 'No foreign key constraints found for target tables.';
END
GO

-- Step 3: Drop indexes (if any specific ones need to be dropped first)
PRINT '=== DROPPING INDEXES IF NEEDED ===';

-- Drop any problematic indexes on target tables
DECLARE @idx_sql NVARCHAR(MAX) = '';
SELECT @idx_sql = @idx_sql + 
    'DROP INDEX [' + i.name + '] ON [' + SCHEMA_NAME(t.schema_id) + '].[' + t.name + '];' + CHAR(13)
FROM sys.indexes i
JOIN sys.tables t ON i.object_id = t.object_id
WHERE t.name IN ('DeviceReadings', 'DeviceImages', 'DeviceImageDetails', 'ComputerVision', 'SnowDepthReadings')
  AND i.is_primary_key = 0
  AND i.is_unique_constraint = 0
  AND i.type > 0;  -- Exclude heaps

IF @idx_sql != ''
BEGIN
    PRINT 'Dropping non-clustered indexes:';
    PRINT @idx_sql;
    -- Uncomment next line if you want to drop indexes (usually not necessary)
    -- EXEC sp_executesql @idx_sql;
    PRINT 'Index dropping skipped (usually not needed for table drops).';
END
GO

-- Step 4: Drop tables in proper order
PRINT '=== DROPPING TABLES ===';

-- Drop DeviceReadings table
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[DeviceReadings]') AND type in (N'U'))
BEGIN
    PRINT 'Dropping DeviceReadings table...';
    DROP TABLE [dbo].[DeviceReadings];
    PRINT 'DeviceReadings table dropped successfully.';
END
ELSE
BEGIN
    PRINT 'DeviceReadings table does not exist or already dropped.';
END
GO

-- Drop DeviceImageDetails table (drop child table first)
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[DeviceImageDetails]') AND type in (N'U'))
BEGIN
    PRINT 'Dropping DeviceImageDetails table...';
    DROP TABLE [dbo].[DeviceImageDetails];
    PRINT 'DeviceImageDetails table dropped successfully.';
END
ELSE
BEGIN
    PRINT 'DeviceImageDetails table does not exist or already dropped.';
END
GO

-- Drop DeviceImages table
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[DeviceImages]') AND type in (N'U'))
BEGIN
    PRINT 'Dropping DeviceImages table...';
    DROP TABLE [dbo].[DeviceImages];
    PRINT 'DeviceImages table dropped successfully.';
END
ELSE
BEGIN
    PRINT 'DeviceImages table does not exist or already dropped.';
END
GO

-- Drop ComputerVision table
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[ComputerVision]') AND type in (N'U'))
BEGIN
    PRINT 'Dropping ComputerVision table...';
    DROP TABLE [dbo].[ComputerVision];
    PRINT 'ComputerVision table dropped successfully.';
END
ELSE
BEGIN
    PRINT 'ComputerVision table does not exist or already dropped.';
END
GO

-- Drop SnowDepthReadings table
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[SnowDepthReadings]') AND type in (N'U'))
BEGIN
    PRINT 'Dropping SnowDepthReadings table...';
    DROP TABLE [dbo].[SnowDepthReadings];
    PRINT 'SnowDepthReadings table dropped successfully.';
END
ELSE
BEGIN
    PRINT 'SnowDepthReadings table does not exist or already dropped.';
END
GO

-- Step 5: Verify all tables are dropped
PRINT '=== VERIFICATION ===';
SELECT 
    CASE 
        WHEN OBJECT_ID(N'[dbo].[DeviceReadings]') IS NULL THEN 'DROPPED'
        ELSE 'EXISTS'
    END as DeviceReadings_Status,
    CASE 
        WHEN OBJECT_ID(N'[dbo].[DeviceImages]') IS NULL THEN 'DROPPED'
        ELSE 'EXISTS'
    END as DeviceImages_Status,
    CASE 
        WHEN OBJECT_ID(N'[dbo].[DeviceImageDetails]') IS NULL THEN 'DROPPED'
        ELSE 'EXISTS'
    END as DeviceImageDetails_Status,
    CASE 
        WHEN OBJECT_ID(N'[dbo].[ComputerVision]') IS NULL THEN 'DROPPED'
        ELSE 'EXISTS'
    END as ComputerVision_Status,
    CASE 
        WHEN OBJECT_ID(N'[dbo].[SnowDepthReadings]') IS NULL THEN 'DROPPED'
        ELSE 'EXISTS'
    END as SnowDepthReadings_Status;

PRINT '=== TABLE DROP OPERATIONS COMPLETED ===';
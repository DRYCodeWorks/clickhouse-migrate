-- Shrink database files with dynamic file name detection
-- This script automatically finds the correct file names and handles shrinking properly

PRINT '=== DATABASE FILE SHRINKING SCRIPT ===';
PRINT 'Database: ' + DB_NAME();
PRINT 'Start Time: ' + CONVERT(varchar(30), GETDATE(), 120);
PRINT '';

-- Step 1: Show current database file information
PRINT '=== CURRENT DATABASE FILES ===';
SELECT 
    file_id,
    name AS logical_name,
    physical_name,
    type_desc,
    size/128.0/1024.0 AS size_gb,
    (size/128.0 - CAST(FILEPROPERTY(name, 'SpaceUsed') AS INT)/128.0)/1024.0 AS free_space_gb,
    state_desc,
    growth/128.0 AS growth_mb
FROM sys.database_files
ORDER BY type_desc, file_id;

PRINT '';

-- Step 2: Get log file information and attempt to shrink
PRINT '=== SHRINKING TRANSACTION LOG FILES ===';

DECLARE @log_files TABLE (
    file_id int,
    logical_name nvarchar(260)
);

INSERT INTO @log_files (file_id, logical_name)
SELECT file_id, name
FROM sys.database_files 
WHERE type = 1; -- Log files

DECLARE @log_name nvarchar(260);
DECLARE @log_id int;
DECLARE @sql nvarchar(max);

DECLARE log_cursor CURSOR FOR
SELECT file_id, logical_name FROM @log_files;

OPEN log_cursor;
FETCH NEXT FROM log_cursor INTO @log_id, @log_name;

WHILE @@FETCH_STATUS = 0
BEGIN
    BEGIN TRY
        PRINT 'Attempting to shrink log file: ' + @log_name + ' (ID: ' + CAST(@log_id AS varchar(10)) + ')';
        
        -- Try to shrink to 1GB (1024 MB)
        DBCC SHRINKFILE(@log_name, 1024);
        PRINT 'Successfully shrunk log file: ' + @log_name;
        
    END TRY
    BEGIN CATCH
        PRINT 'Warning: Could not shrink log file ' + @log_name + ': ' + ERROR_MESSAGE();
        
        -- Try alternative approach - shrink by percentage
        BEGIN TRY
            PRINT 'Attempting percentage-based shrink for: ' + @log_name;
            DBCC SHRINKFILE(@log_name, TRUNCATEONLY);
            PRINT 'Truncate-only shrink completed for: ' + @log_name;
        END TRY
        BEGIN CATCH
            PRINT 'Error: Could not shrink log file ' + @log_name + ' using any method: ' + ERROR_MESSAGE();
        END CATCH
    END CATCH
    
    FETCH NEXT FROM log_cursor INTO @log_id, @log_name;
END

CLOSE log_cursor;
DEALLOCATE log_cursor;

PRINT '';

-- Step 3: Shrink data files
PRINT '=== SHRINKING DATA FILES ===';

DECLARE @data_files TABLE (
    file_id int,
    logical_name nvarchar(260),
    current_size_gb decimal(10,2),
    used_space_gb decimal(10,2),
    free_space_gb decimal(10,2)
);

INSERT INTO @data_files (file_id, logical_name, current_size_gb, used_space_gb, free_space_gb)
SELECT 
    file_id,
    name,
    size/128.0/1024.0,
    CAST(FILEPROPERTY(name, 'SpaceUsed') AS INT)/128.0/1024.0,
    (size/128.0 - CAST(FILEPROPERTY(name, 'SpaceUsed') AS INT)/128.0)/1024.0
FROM sys.database_files 
WHERE type = 0; -- Data files

DECLARE @data_name nvarchar(260);
DECLARE @data_id int;
DECLARE @current_size_gb decimal(10,2);
DECLARE @used_space_gb decimal(10,2);
DECLARE @free_space_gb decimal(10,2);
DECLARE @target_size_mb int;

DECLARE data_cursor CURSOR FOR
SELECT file_id, logical_name, current_size_gb, used_space_gb, free_space_gb 
FROM @data_files;

OPEN data_cursor;
FETCH NEXT FROM data_cursor INTO @data_id, @data_name, @current_size_gb, @used_space_gb, @free_space_gb;

WHILE @@FETCH_STATUS = 0
BEGIN
    -- Calculate target size (used space + 10% buffer, minimum 1GB)
    SET @target_size_mb = CASE 
        WHEN (@used_space_gb * 1.1 * 1024) < 1024 THEN 1024 
        ELSE CAST((@used_space_gb * 1.1 * 1024) AS int)
    END;
    
    PRINT 'Data file: ' + @data_name;
    PRINT '  Current size: ' + CAST(@current_size_gb AS varchar(20)) + ' GB';
    PRINT '  Used space: ' + CAST(@used_space_gb AS varchar(20)) + ' GB';
    PRINT '  Free space: ' + CAST(@free_space_gb AS varchar(20)) + ' GB';
    PRINT '  Target size: ' + CAST(@target_size_mb AS varchar(20)) + ' MB';
    
    IF @free_space_gb > 0.5 -- Only shrink if more than 500MB free
    BEGIN
        BEGIN TRY
            DBCC SHRINKFILE(@data_name, @target_size_mb);
            PRINT '  Successfully shrunk data file: ' + @data_name;
        END TRY
        BEGIN CATCH
            PRINT '  Warning: Could not shrink data file ' + @data_name + ': ' + ERROR_MESSAGE();
            
            -- Try truncate-only approach
            BEGIN TRY
                DBCC SHRINKFILE(@data_name, TRUNCATEONLY);
                PRINT '  Truncate-only shrink completed for: ' + @data_name;
            END TRY
            BEGIN CATCH
                PRINT '  Error: Could not shrink data file using any method: ' + ERROR_MESSAGE();
            END CATCH
        END CATCH
    END
    ELSE
    BEGIN
        PRINT '  Skipped (insufficient free space to warrant shrinking)';
    END
    
    PRINT '';
    FETCH NEXT FROM data_cursor INTO @data_id, @data_name, @current_size_gb, @used_space_gb, @free_space_gb;
END

CLOSE data_cursor;
DEALLOCATE data_cursor;

-- Step 4: Show final database file sizes
PRINT '=== FINAL DATABASE FILE SIZES ===';
SELECT 
    file_id,
    name AS logical_name,
    type_desc,
    size/128.0/1024.0 AS size_gb,
    (size/128.0 - CAST(FILEPROPERTY(name, 'SpaceUsed') AS INT)/128.0)/1024.0 AS free_space_gb,
    CAST(FILEPROPERTY(name, 'SpaceUsed') AS INT)/128.0/1024.0 AS used_space_gb,
    CAST((CAST(FILEPROPERTY(name, 'SpaceUsed') AS FLOAT) / size) * 100 AS decimal(5,2)) AS percent_used
FROM sys.database_files
ORDER BY type_desc, file_id;

-- Step 5: Show total database size summary
PRINT '';
PRINT '=== DATABASE SIZE SUMMARY ===';
EXEC sp_spaceused;

PRINT '';
PRINT 'Shrink operations completed at: ' + CONVERT(varchar(30), GETDATE(), 120);
PRINT '=== SHRINK SCRIPT COMPLETED ===';

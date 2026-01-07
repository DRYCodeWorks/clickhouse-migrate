-- After running the DBCC Shrink database, and getting the errors in ShrinkFailed.md, this reduced the database file size like so

-- database_name	database_size	unallocated space
-- frost-db-prd	    350056.00 MB	66888.84 MB

-- reserved	        data	        index_size	    unused
-- 289905824 KB	    171526792 KB	118097000 KB	282032 KB

DBCC SHRINKFILE('FrostTechDevicePortalDB-Production2', 300000)
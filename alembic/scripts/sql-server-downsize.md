# Frost RDS SQL Server Storage Reduction Plan
## Reducing from 6000GB to ~400GB

### Executive Summary
- **Current Instances:** 
  - Production: `frost-db-prd` (5970GB, db.r6i.2xlarge)
  - Development: `tf-frost-db-dev` (6000GB, db.t3.medium) 
  - Staging: `tf-frost-db-stg` (6000GB, db.t3.medium)
- **Database:** `frost-db-prd` (56 tables + views)
- **SQL Server Version:** 15.00.4410.1.v1 (SQL Server 2019)
- **Target State:** 400-450GB allocated storage per environment
- **Estimated Savings:** $1,200-1,300/month per instance
- **Method:** Native SQL Server backup to S3, restore to new smaller RDS instance
- **Estimated Downtime:** 30 minutes (with differential) to 4 hours (full cutover)

---

## Phase 1: Prerequisites & Setup (No Downtime)

### 1.1 Create S3 Bucket for Backups

```bash
# Create bucket with versioning for safety (use appropriate environment suffix)
aws s3 mb s3://frost-rds-migration-backup-dev  # For development
# aws s3 mb s3://frost-rds-migration-backup-stg  # For staging
# aws s3 mb s3://frost-rds-migration-backup-prd  # For production

# Enable versioning
BUCKET_NAME="frost-rds-migration-backup-dev"  # Change for each environment
aws s3api put-bucket-versioning \
    --bucket $BUCKET_NAME \
    --versioning-configuration Status=Enabled

# Optional: Enable lifecycle to delete old backups after 30 days
# cat > lifecycle.json << EOF
# {
#     "Rules": [{
#         "Filter": {
#           "Prefix": ""
#         },
#         "Expiration": {
#             "Days": 30
#         }
#     }]
# }
# EOF

aws s3api put-bucket-lifecycle-configuration \
    --bucket $BUCKET_NAME \
    --lifecycle-configuration file://lifecycle.json
```

### 1.2 Create IAM Role for RDS S3 Access

```bash
# # Create trust policy
# cat > trust-policy.json << EOF
# {
#   "Version": "2012-10-17",
#   "Statement": [
#     {
#       "Effect": "Allow",
#       "Principal": {
#         "Service": "rds.amazonaws.com"
#       },
#       "Action": "sts:AssumeRole"
#     }
#   ]
# }
# EOF

# Create the role
aws iam create-role \
    --role-name rds-s3-backup-restore-role \
    --assume-role-policy-document file://trust-policy.json

# Create S3 access policy
# cat > s3-policy.json << EOF
# {
#   "Version": "2012-10-17",
#   "Statement": [
#     {
#       "Effect": "Allow",
#       "Action": [
#         "s3:GetObject",
#         "s3:PutObject",
#         "s3:ListBucket",
#         "s3:GetBucketLocation",
#         "s3:DeleteObject"
#       ],
#       "Resource": [
#         "arn:aws:s3:::frost-rds-migration-backup-*/*",
#         "arn:aws:s3:::frost-rds-migration-backup-*"
#       ]
#     }
#   ]
# }
# EOF

# Attach policy to role
aws iam put-role-policy \
    --role-name rds-s3-backup-restore-role \
    --policy-name S3BackupRestorePolicy \
    --policy-document file://s3-policy.json
```

### 1.3 Create and Configure Option Group

```bash
# Get your SQL Server version first
# For development:
aws rds describe-db-instances \
    --db-instance-identifier tf-frost-db-dev \
    --query 'DBInstances[0].EngineVersion'
# Output: "15.00.4410.1.v1"

# Create option group (adjust version as needed)
aws rds create-option-group \
    --option-group-name sql-server-backup-restore \
    --engine-name sqlserver-web \
    --major-engine-version "15.00" \
    --option-group-description "Native backup and restore to S3"

# Get your AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Add backup/restore option
aws rds add-option-to-option-group \
    --option-group-name sql-server-backup-restore \
    --options "OptionName=SQLSERVER_BACKUP_RESTORE,OptionSettings=[{Name=IAM_ROLE_ARN,Value=arn:aws:iam::${AWS_ACCOUNT_ID}:role/rds-s3-backup-restore-role}]"
 
# Apply to your current instance (may cause brief interruption)
# For development:
aws rds modify-db-instance \
    --db-instance-identifier tf-frost-db-dev \
    --option-group-name sql-server-backup-restore \
    --apply-immediately

# Wait for the modification to complete
aws rds wait db-instance-available \
    --db-instance-identifier tf-frost-db-dev
```

---

## Phase 2: Testing & Validation

### 2.1 Test Backup Process with Small Database

```sql
-- Connect to your RDS instance via SSMS or Azure Data Studio
-- Create a test database
CREATE DATABASE backup_test;
GO

-- Test backup functionality
EXEC msdb.dbo.rds_backup_database 
    @source_db_name='backup_test',
    @s3_arn_to_backup_to='arn:aws:s3:::frost-rds-migration-backup-dev/test-backup.bak',
    @overwrite_s3_backup_file=1;

-- Check task status
EXEC msdb.dbo.rds_task_status;
--  Should see IN_PROGRESS or SUCCESS

-- Clean up test
DROP DATABASE backup_test;
```

### 2.2 Verify Current Database Size

```sql
-- Check actual database size after shrinking
SELECT 
    DB_NAME() as DatabaseName,
    name AS FileName,
    size/128.0/1024.0 AS CurrentSizeGB,
    (size/128.0 - CAST(FILEPROPERTY(name, 'SpaceUsed') AS INT)/128.0)/1024.0 AS FreeSpaceGB,
    type_desc,
    state_desc
FROM sys.database_files;

-- Get total database size
EXEC sp_spaceused;

-- Table-by-table breakdown (optional)
SELECT 
    t.NAME AS TableName,
    s.Name AS SchemaName,
    p.rows AS RowCounts,
    SUM(a.total_pages) * 8/1024/1024 AS TotalSpaceGB, 
    SUM(a.used_pages) * 8/1024/1024 AS UsedSpaceGB, 
    (SUM(a.total_pages) - SUM(a.used_pages)) * 8/1024/1024 AS UnusedSpaceGB
FROM sys.tables t
INNER JOIN sys.indexes i ON t.OBJECT_ID = i.object_id
INNER JOIN sys.partitions p ON i.object_id = p.OBJECT_ID AND i.index_id = p.index_id
INNER JOIN sys.allocation_units a ON p.partition_id = a.container_id
LEFT OUTER JOIN sys.schemas s ON t.schema_id = s.schema_id
WHERE t.NAME NOT LIKE 'dt%' AND t.is_ms_shipped = 0 AND i.OBJECT_ID > 255 
GROUP BY t.Name, s.Name, p.Rows
ORDER BY TotalSpaceGB DESC;
```

---

## Phase 2.5: Drop Large Tables and Free Storage (DOWNTIME REQUIRED)

⚠️ **WARNING: This phase requires application downtime as it involves dropping tables**

### 2.5.1 Check Table Activity (Optional but Recommended)

Before dropping tables, verify they are not actively being written to:

```bash
# Execute the table activity monitoring script
sqlcmd -S your-server -d frost-db-prd -i scripts/check-table-activity.sql
```

**Script Location:** `scripts/check-table-activity.sql`

This script will check for:
- Active sessions accessing the tables
- Recent write activity 
- Current locks
- Foreign key dependencies

### 2.5.2 Drop Target Tables

Execute the comprehensive table drop script that handles all dependencies:

```bash
# Execute the dependency-aware table drop script
sqlcmd -S your-server -d frost-db-prd -i scripts/drop-tables-with-dependencies.sql
```

**Script Location:** `scripts/drop-tables-with-dependencies.sql`

This script will:
1. Drop dependent views (including `vw_DeviceReadings`)
2. Remove foreign key constraints
3. Drop tables in proper order:
   - DeviceReadings
   - DeviceImageDetails (child table first)
   - DeviceImages  
   - ComputerVision
   - SnowDepthReadings
4. Verify all tables are dropped successfully

### 2.5.3 Free Up Storage Space with DBCC Commands

Execute the intelligent database shrinking script that automatically detects file names and handles errors:

```bash
# Execute the database shrinking script
sqlcmd -S your-server -d frost-db-prd -i scripts/shrink-database-files.sql
```

**Script Location:** `scripts/shrink-database-files.sql`

⚠️ **IMPORTANT:** For large databases, consider running each step of the shrink script manually/separately:
1. **Step 1:** Review current file sizes first
2. **Step 2:** Shrink log files (can be time-consuming)  
3. **Step 3:** Shrink data files (monitor progress closely)
4. **Step 4:** Verify final results

This allows you to:
- Monitor progress of each operation
- Stop/restart if needed
- Address specific issues that arise
- Ensure each step completes successfully before proceeding

This script will:
1. **Detect actual file names** dynamically (no hardcoded names)
2. **Show current file sizes** before shrinking
3. **Shrink transaction logs** with error handling
4. **Shrink data files** intelligently (only if >500MB free space)
5. **Provide detailed progress** and error messages
6. **Show final sizes** and space savings

**Key advantages over manual DBCC commands:**
- ✅ No file name guessing - finds actual logical names
- ✅ Intelligent sizing (used space + 10% buffer)
- ✅ Error handling for common issues
- ✅ Skips unnecessary operations
- ✅ Comprehensive reporting

## Phase 3: Full Backup to S3

### 3.1 Initiate Full Backup with Compression

```sql
-- Start full backup with compression (CRITICAL for 6144GB → 350GB database)
DECLARE @S3_ARN varchar(2000);
SET @S3_ARN = 'arn:aws:s3:::frost-rds-migration-backup/frost-db-prd-full-' 
              + CONVERT(varchar(10), GETDATE(), 112) + '.bak';

EXEC msdb.dbo.rds_backup_database 
    @source_db_name='frost-db-prd',
    @s3_arn_to_backup_to=@S3_ARN,
    @overwrite_s3_backup_file=1,
    @type='FULL',
    @compression='GZIP';  -- Essential for large databases

-- Get the task ID from the output
-- Note the task_id for monitoring
```

### 3.2 Monitor Backup Progress

```sql
-- Check backup progress (run periodically)
EXEC msdb.dbo.rds_task_status @db_name='frost-db-prd';

-- Or check all tasks
EXEC msdb.dbo.rds_task_status;

-- Detailed task information
SELECT * FROM msdb.dbo.rds_fn_task_status(NULL, NULL)
WHERE database_name = 'frost-db-prd'
ORDER BY created_at DESC;
```

**Estimated Time:** 
- 350GB database with GZIP compression → 50-150GB backup file
- Upload to S3: 1-3 hours depending on instance type and network

---

## Phase 4: Create New RDS Instance

### 4.1 Create New Instance with Smaller Storage

Execute the automated RDS instance creation script:

```bash
# Interactive mode with public access (default)
./scripts/create-rds-instance.sh

# Custom parameters with public access
./scripts/create-rds-instance.sh tf-frost-db-dev2 tf-frost-db-dev 50 100 true

# Private instance (VPC access only)
./scripts/create-rds-instance.sh tf-frost-db-dev2 tf-frost-db-dev 50 100 false

# Fully automated mode with public access (USE WITH CAUTION)
./scripts/create-rds-instance.sh tf-frost-db-dev2 tf-frost-db-dev 50 100 true true

# Arguments: [new_instance_name] [source_instance_name] [initial_storage_gb] [max_storage_gb] [publicly_accessible] [auto_approve]
```

**Script Location:** `scripts/create-rds-instance.sh`

This script will:

1. **Auto-detect configuration** from existing instance:
   - VPC Security Groups
   - DB Subnet Group  
   - KMS Key ID
   - Parameter Groups
   - Engine Version

2. **Create Secrets Manager secret** with:
   - 32-character secure password
   - Auto-rotation capability
   - KMS encryption

3. **Create new RDS instance** with:
   - Smaller storage (50GB initial, 100GB max auto-scaling)
   - Production-ready configuration
   - Enhanced monitoring and Performance Insights
   - Proper tags and deletion protection

4. **Wait for availability** and provide connection details

**Key features:**
- ✅ **Error handling** with colored output and validation
- ✅ **Idempotent** - won't recreate existing secrets/instances  
- ✅ **Flexible** - accepts command-line arguments
- ✅ **Safe** - validates all inputs and prerequisites
- ✅ **Complete** - handles all optional parameters automatically

**🛡️ Safety Breakpoints (Interactive Mode):**
1. **Configuration Review** - Verify instance names and storage settings
2. **Extracted Settings** - Confirm auto-detected configuration from source instance
3. **Final Confirmation** - Last chance to abort before creating the instance
4. **Wait Option** - Choose to wait for completion or check status later

**⚠️ Production Safety:**
- Use interactive mode for production environments
- Only use `auto_approve=true` for automated CI/CD pipelines
- Always review extracted configuration before proceeding
- Instance creation is **irreversible** and incurs ongoing costs

---

## Phase 5: Restore Database to New Instance

### 5.1 Connect to New Instance and Restore

```sql
-- On the NEW instance, restore the database
DECLARE @S3_ARN varchar(2000);
SET @S3_ARN = 'arn:aws:s3:::frost-rds-migration-backup-dev/frost-db-prd-full-' 
              + CONVERT(varchar(10), GETDATE(), 112) + '.bak';

EXEC msdb.dbo.rds_restore_database 
    @restore_db_name='frost-db-prd',
    @s3_arn_to_restore_from=@S3_ARN,
    @with_norecovery=1;

-- Monitor restore progress
EXEC msdb.dbo.rds_task_status @db_name='frost-db-prd';
```

### 5.2 Post-Restore Validation and Fixes

**Essential Steps:**

```sql
-- 1. Verify database integrity first
PRINT 'Checking database integrity...';
DBCC CHECKDB('frost-db-prd') WITH NO_INFOMSGS;

-- 2. Check if any users need fixing (common issue)
-- this must be done from the frost-db-prd database. There will be orphans
SELECT name, sid FROM sys.database_principals WHERE type = 'S' AND name NOT LIKE '##%';

-- If you see orphaned users, fix them:
python scripts/restore-logins.py --environment dev
```

**Optional Steps (only if needed):**

```sql
-- Check database options (these usually restore correctly)
SELECT name, recovery_model_desc, is_auto_shrink_on, is_auto_update_stats_on 
FROM sys.databases WHERE name = 'frost-db-prd';

-- Only run these if the above query shows incorrect settings:
-- ALTER DATABASE [frost-db-prd] SET RECOVERY SIMPLE;
-- ALTER DATABASE [frost-db-prd] SET AUTO_SHRINK OFF;
-- ALTER DATABASE [frost-db-prd] SET AUTO_UPDATE_STATISTICS ON;

-- Check compatibility level (only change if needed)
SELECT name, compatibility_level FROM sys.databases WHERE name = 'frost-db-prd';
-- ALTER DATABASE [frost-db-prd] SET COMPATIBILITY_LEVEL = 150; -- Only if different

-- Update statistics (SQL Server usually handles this automatically)
-- EXEC sp_updatestats; -- Only if performance issues
```

---

## ⏸️ **PAUSE POINT - VALIDATION REQUIRED**

**🛑 STOP HERE BEFORE CUTOVER**

Before proceeding to Phase 6 (Cutover), ensure the following validation steps are completed:

### Pre-Cutover Checklist:
- [ ] **New RDS instance is running** and accessible
- [ ] **Database restore completed successfully** (verify with Phase 5 validation queries)
- [ ] **Application can connect** to new instance (test connection strings)
- [ ] **Data integrity verified** (row counts, key tables, critical queries)
- [ ] **Performance testing** completed on new instance
- [ ] **Backup/rollback plan** confirmed and documented
- [ ] **Downtime window** scheduled and stakeholders notified
- [ ] **Monitoring** set up for new instance

### Recommended Actions:
1. **Test your application** against the new database thoroughly
2. **Run validation queries** to compare data between old and new instances
3. **Document rollback procedures** in case issues arise
4. **Coordinate with your team** on the cutover timing
5. **Prepare connection string updates** for your applications

### When Ready to Continue:
- Schedule the cutover during your planned maintenance window
- Ensure all team members are available for the cutover
- Have rollback procedures ready and tested

**⚠️ The next phase involves changing production traffic to the new database. This is the point of no return for your migration.**

---

## Phase 6: Cutover Strategy

### Option A: Minimal Downtime with Differential Backup

```sql
-- 1. ON SOURCE: Stop new writes (set to read-only)
ALTER DATABASE [frost-db-prd] SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
ALTER DATABASE [frost-db-prd] SET READ_ONLY WITH ROLLBACK IMMEDIATE;
ALTER DATABASE [frost-db-prd] SET MULTI_USER;

-- 2. Take differential backup
DECLARE @S3_ARN_DIFF varchar(2000);
SET @S3_ARN_DIFF = 'arn:aws:s3:::frost-rds-migration-backup-dev/frost-db-prd-diff-' 
                   + CONVERT(varchar(10), GETDATE(), 112) + '.bak';

EXEC msdb.dbo.rds_backup_database 
    @source_db_name='frost-db-prd',
    @s3_arn_to_backup_to=@S3_ARN_DIFF,
    @type='DIFFERENTIAL';

EXEC msdb.dbo.rds_task_status @db_name='frost-db-prd';

-- 3. ON TARGET: Restore differential
EXEC msdb.dbo.rds_restore_database 
    @restore_db_name='frost-db-prd',
    @s3_arn_to_restore_from=@S3_ARN_DIFF,
    @type='DIFFERENTIAL',
    @with_norecovery=0;


-- We'll wait for he "backup" status to switch to "available" in RDS

-- 4. Update application connection strings
-- We should only need to update the RDS proxy here


-- 5. ON SOURCE: Set back to read-write (for rollback if needed)
-- NOTE: !!!!!!!!! this needs to be done on target as well
ALTER DATABASE [frost-db-prd] SET READ_WRITE;
```

## Phase 7: Validation & Cleanup

### 7.1 Validation Queries

```sql
-- Compare row counts between old and new
SELECT 
    OBJECT_NAME(object_id) AS TableName,
    SUM(rows) AS RowCount
FROM sys.partitions
WHERE index_id IN (0, 1)
GROUP BY object_id
ORDER BY RowCount DESC;

-- Check database size on new instance
EXEC sp_spaceused;

-- Verify all objects exist
SELECT type_desc, COUNT(*) as count
FROM sys.objects
WHERE is_ms_shipped = 0
GROUP BY type_desc
ORDER BY type_desc;

-- Test application critical queries
-- [Add your specific validation queries here]
```

### 7.2 Cleanup Tasks

```bash
# After successful validation (wait 24-48 hours):

# 1. Take final snapshot of old instance
aws rds create-db-snapshot \
    --db-instance-identifier OLD_INSTANCE \
    --db-snapshot-identifier old-instance-final-snapshot

# 2. Stop old instance (keep for 7 days as safety)
aws rds stop-db-instance \
    --db-instance-identifier OLD_INSTANCE

# 3. After confidence period, delete old instance
aws rds delete-db-instance \
    --db-instance-identifier OLD_INSTANCE \
    --skip-final-snapshot \
    --delete-automated-backups

# 4. Resize new instance to appropriate size if needed
aws rds modify-db-instance \
    --db-instance-identifier $NEW_INSTANCE_NAME \
    --db-instance-class db.m5.2xlarge \
    --apply-immediately

# 5. Clean up S3 backups
aws s3 rm s3://frost-rds-migration-backup-dev/ --recursive
```

---

## Automation Script Template

```bash
#!/bin/bash
# rds-migration.sh - Automate RDS migration process

set -e

# Configuration
SOURCE_INSTANCE="current-instance"
TARGET_INSTANCE="new-instance"
S3_BUCKET="frost-rds-migration-backup-dev"
DATABASE_NAME="frost-db-prd"
TARGET_STORAGE_GB="450"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

# Function to check backup status
check_backup_status() {
    local task_id=$1
    while true; do
        status=$(aws rds describe-db-instances \
            --db-instance-identifier $SOURCE_INSTANCE \
            --query 'DBInstances[0].StatusInfos[?StatusType==`backup`].Status' \
            --output text)
        
        if [ "$status" = "completed" ]; then
            log "Backup completed successfully"
            break
        elif [ "$status" = "failed" ]; then
            error "Backup failed"
        else
            log "Backup in progress... ($status)"
            sleep 60
        fi
    done
}

# Main migration flow
main() {
    log "Starting RDS migration from $SOURCE_INSTANCE to $TARGET_INSTANCE"
    
    # Phase 1: Pre-checks
    log "Running pre-flight checks..."
    aws rds describe-db-instances --db-instance-identifier $SOURCE_INSTANCE > /dev/null || error "Source instance not found"
    
    # Phase 2: Backup
    log "Initiating backup to S3..."
    BACKUP_FILE="s3://${S3_BUCKET}/${DATABASE_NAME}-$(date +%Y%m%d-%H%M%S).bak"
    # [Add SQL backup command execution here]
    
    # Phase 3: Create new instance
    log "Creating new RDS instance with ${TARGET_STORAGE_GB}GB storage..."
    # [Add instance creation here]
    
    # Phase 4: Restore
    log "Restoring database to new instance..."
    # [Add restore commands here]
    
    # Phase 5: Validation
    log "Running validation checks..."
    # [Add validation here]
    
    log "Migration completed successfully!"
}

# Run main function
main "$@"
```

---

## Timeline & Estimates

| Phase | Duration | Downtime Required |
|-------|----------|------------------|
| Setup & Prerequisites | 1-2 hours | No |
| Test Backup | 30 minutes | No |
| **Drop Tables & DBCC** | **30-60 minutes** | **Yes** |
| Full Backup (350GB) | 2-3 hours | No |
| Create New Instance | 30 minutes | No |
| Restore Database | 2-3 hours | No |
| Validation Testing | 1-2 hours | No |
| **Cutover** | **30 min - 4 hours** | **Yes** |
| Post-validation | 1 hour | No |

**Total Project Time:** 9-13 hours of work
**Actual Downtime:** 1-5 hours (table drops + cutover)

---

## Risk Mitigation

### Rollback Plan
1. Keep old instance running for 48 hours minimum
2. Take snapshot before starting
3. Test rollback procedure: Update connection strings back to old instance
4. Document all configuration differences

### Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Backup fails with permissions error | Verify IAM role and S3 bucket policy |
| Restore fails with "database exists" | Drop existing database first |
| Orphaned users after restore | Run `sp_change_users_login 'Auto_Fix', 'username'` |
| Performance issues after migration | Update statistics and rebuild indexes |
| Connection timeouts during restore | Normal for large databases; monitor with `rds_task_status` |

---

## Cost Analysis

### Current Costs (6000GB)
- Storage: 6000GB × $0.23/GB = **$1,380/month**
- IOPS (if provisioned): Additional costs

### New Costs (450GB)
- Storage: 450GB × $0.23/GB = **$103.50/month**
- One-time migration costs: ~$50 (S3 storage, extra instance hours)

### **Monthly Savings: ~$1,276.50**
### **Annual Savings: ~$15,318**

---

## Final Checklist

- [ ] S3 bucket created with proper permissions
- [ ] IAM role created and attached
- [ ] Option group configured and applied
- [ ] Test backup successful
- [ ] **Application downtime scheduled for table drops**
- [ ] **Table activity check completed** (`scripts/check-table-activity.sql`)
- [ ] **Table drops completed** (`scripts/drop-tables-with-dependencies.sql`)
- [ ] **All 5 tables dropped** (DeviceReadings, DeviceImageDetails, DeviceImages, ComputerVision, SnowDepthReadings)
- [ ] **DBCC SHRINKFILE and SHRINKDATABASE executed**
- [ ] **Database size reduced to ~350-400GB**
- [ ] Full backup completed
- [ ] New instance created
- [ ] Database restored successfully
- [ ] Application connection strings updated
- [ ] Validation queries passed
- [ ] Monitoring configured on new instance
- [ ] Old instance snapshot taken
- [ ] Documentation updated
- [ ] Team notified of new endpoint
- [ ] Old instance scheduled for deletion

---

## Support Commands Quick Reference

```sql
-- Check backup/restore tasks
EXEC msdb.dbo.rds_task_status;

-- Cancel a running task
EXEC msdb.dbo.rds_cancel_task @task_id = <task_id>;

-- Show S3 integration status
EXEC msdb.dbo.rds_show_configuration;

-- Database size check
EXEC sp_spaceused;
```

```bash
# Check instance status
aws rds describe-db-instances --db-instance-identifier INSTANCE_NAME

# Monitor CloudWatch metrics
aws cloudwatch get-metric-statistics \
    --namespace AWS/RDS \
    --metric-name FreeStorageSpace \
    --dimensions Name=DBInstanceIdentifier,Value=INSTANCE_NAME \
    --start-time 2024-01-01T00:00:00Z \
    --end-time 2024-01-02T00:00:00Z \
    --period 3600 \
    --statistics Average
```

---

## Notes for Claude Code Implementation

When implementing with Claude Code:
1. Start by setting up the AWS infrastructure (S3, IAM)
2. Create a Python/Bash script to orchestrate the migration
3. Add comprehensive error handling and logging
4. Implement progress monitoring using AWS SDK
5. Create a rollback script as a safety measure
6. Consider using AWS Step Functions for complex orchestration
7. Add CloudWatch alarms for migration monitoring

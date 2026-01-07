# RDS Downsizing Quick Start Guide 🚀

> Simple guide to downsize your Frost RDS SQL Server instance from 6TB to ~450GB

## Project Overview

**Goal**: Reduce storage costs by ~$1,270/month per environment  
**Method**: Native SQL Server backup → restore to smaller RDS instance  
**Target**: Development environment (`tf-frost-db-dev`)  
**Timeline**: 8-12 hours total work, 30min-4hr downtime  

## Prerequisites ✅

### 1. Environment Setup
```bash
# Ensure AWS profile is set
export AWS_PROFILE=FrostAdmin

# Install Python dependencies
pip install boto3 tabulate

# Verify Python virtual environment is active
python --version  # Should show Python 3.x
```

### 2. Verify Current Status
```bash
# Check that you're in the db-scripts directory
pwd  # Should show: .../Frost/db-scripts

# List available scripts
ls scripts/
```

## Quick Start - Development Environment

### Step 1: Pre-flight Validation (5 minutes)
```bash
cd scripts/
python3 rds-preflight-check.py \
  --source-instance tf-frost-db-dev \
  --s3-bucket frost-rds-migration-backup-dev \
  --environment dev
```
**✅ Expected**: All checks pass with green status  
**❌ If failed**: See detailed guide in `sql-server-downsize.md` for troubleshooting

### Step 2: Run Complete Migration (8-10 hours)
```bash
./rds-migration-orchestrator.sh dev
```

This script will interactively guide you through:
- **Phase 1**: Setup prerequisites (S3 bucket, IAM roles)
- **Phase 2**: Create compressed backup to S3 (2-3 hours)
- **Phase 3**: Create new RDS instance with 450GB storage (30 min)
- **Phase 4**: Restore database to new instance (2-3 hours)
- **Phase 5**: Validation and testing (1-2 hours)

### Step 3: Manual SQL Commands (when prompted)

The orchestrator will generate SQL commands for you to run. Connect to the appropriate RDS instance using your preferred SQL client (SSMS, Azure Data Studio, etc.).

**Backup command** (run on source instance):
```sql
EXEC msdb.dbo.rds_backup_database 
    @source_db_name='frost-db-prd',
    @s3_arn_to_backup_to='arn:aws:s3:::frost-rds-migration-backup-dev/backup-file.bak',
    @type='FULL',
    @compression='GZIP';
```

**Monitor progress**:
```sql
EXEC msdb.dbo.rds_task_status;
```

**Restore command** (run on new instance):
```sql
EXEC msdb.dbo.rds_restore_database 
    @restore_db_name='frost-db-prd',
    @s3_arn_to_restore_from='arn:aws:s3:::frost-rds-migration-backup-dev/backup-file.bak';
```

## Development Environment Settings

| Setting | Value |
|---------|-------|
| Source Instance | `tf-frost-db-dev` |
| New Instance | `tf-frost-db-dev-downsized` |
| Database | `frost-db-prd` |
| S3 Bucket | `frost-rds-migration-backup-dev` |
| Target Storage | 450GB |
| Instance Class | db.t3.medium |

## Validation Checklist

After migration, verify these items:

- [ ] Database restored successfully
- [ ] Row counts match between old/new instances
- [ ] Application can connect to new instance
- [ ] Database size is ~450GB (run `EXEC sp_spaceused;`)
- [ ] All tables and views present
- [ ] Test critical application queries

## Rollback Plan 🔙

**If something goes wrong:**

1. **Source instance still exists** → Update connection strings back to original
2. **Take snapshot** before deleting old instance:
   ```bash
   aws rds create-db-snapshot \
     --db-instance-identifier tf-frost-db-dev \
     --db-snapshot-identifier dev-pre-migration-snapshot
   ```
3. **Keep old instance running for 48+ hours** after successful cutover

## Logs and Troubleshooting 🔍

**Log location**: `scripts/logs/migration_dev_YYYYMMDD_HHMMSS.log`

**Common issues**:
- **Permission errors**: Check IAM role and S3 bucket policies
- **Backup/restore timeouts**: Normal for large databases, monitor with `rds_task_status`
- **Connection failures**: Verify security groups and VPC settings

**Support commands**:
```bash
# Check RDS instance status
aws rds describe-db-instances --db-instance-identifier tf-frost-db-dev

# Cancel a running task (if needed)
# Connect to SQL Server and run:
# EXEC msdb.dbo.rds_cancel_task @task_id = <task_id>;
```

## Cost Savings 💰

**Current cost**: 6000GB × $0.23/GB = **$1,380/month**  
**New cost**: 450GB × $0.23/GB = **$103.50/month**  
**Monthly savings**: **~$1,276.50**  
**Annual savings**: **~$15,318**  

## Next Steps

After successful dev migration:
1. Document any issues encountered
2. Plan staging environment migration
3. Schedule production migration during maintenance window

---

## Reference Documentation

- **Complete technical guide**: `sql-server-downsize.md` (640 lines of detailed procedures)
- **Script documentation**: `scripts/README.md` (individual script usage)
- **Automation scripts**: `scripts/` directory (5 Python/Bash tools)

---

## Quick Commands Reference

```bash
# Start migration
./scripts/rds-migration-orchestrator.sh dev

# Check pre-requisites
python3 scripts/rds-preflight-check.py --source-instance tf-frost-db-dev --s3-bucket frost-rds-migration-backup-dev --environment dev

# Individual backup (if needed)
python3 scripts/rds-backup.py --instance tf-frost-db-dev --database frost-db-prd --bucket frost-rds-migration-backup-dev --environment dev --type FULL --compression

# Individual restore (if needed)
python3 scripts/rds-restore.py --source-instance tf-frost-db-dev --new-instance tf-frost-db-dev-downsized --database frost-db-prd --bucket frost-rds-migration-backup-dev --storage-gb 450 --environment dev
```

**Ready to start? Run the pre-flight check first!** ⬆️
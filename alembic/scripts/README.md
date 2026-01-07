# Frost RDS SQL Server Migration Scripts

Automated scripts for downsizing RDS SQL Server instances from 6TB to ~400GB.

## Prerequisites

```bash
pip install boto3 tabulate
export AWS_PROFILE=FrostAdmin
```

## Quick Start

### 1. Run Preflight Checks
```bash
python3 rds-preflight-check.py \
  --source-instance tf-frost-db-dev \
  --s3-bucket frost-rds-migration-backup-dev \
  --environment dev
```

### 2. Run Complete Migration
```bash
./rds-migration-orchestrator.sh dev
```

## Individual Scripts

### rds-preflight-check.py
Validates all prerequisites before migration:
- Source instance configuration
- Backup/restore option enabled
- S3 bucket permissions
- IAM role configuration
- Storage metrics and estimates

### rds-backup.py
Creates native SQL Server backups to S3:
```bash
python3 rds-backup.py \
  --instance tf-frost-db-dev \
  --database frost-db-prd \
  --bucket frost-rds-migration-backup-dev \
  --environment dev \
  --type FULL \
  --compression
```

### rds-restore.py
Creates new instance and generates restore commands:
```bash
python3 rds-restore.py \
  --source-instance tf-frost-db-dev \
  --new-instance tf-frost-db-dev-downsized \
  --database frost-db-prd \
  --bucket frost-rds-migration-backup-dev \
  --storage-gb 450 \
  --environment dev
```

### rds-migration-orchestrator.sh
Complete migration workflow with interactive phases:
- Phase 1: Setup prerequisites
- Phase 2: Create backup
- Phase 3: Create new instance
- Phase 4: Restore database
- Phase 5: Validation

## Environment Configuration

| Environment | Source Instance | Storage | Savings/Month |
|------------|----------------|---------|---------------|
| Development | tf-frost-db-dev | 6000GB → 450GB | ~$1,270 |
| Staging | tf-frost-db-stg | 6000GB → 450GB | ~$1,270 |
| Production | frost-db-prd | 5970GB → 450GB | ~$1,270 |

## Migration Timeline

| Phase | Duration | Downtime |
|-------|----------|----------|
| Backup | 2-3 hours | No |
| Instance Creation | 30 minutes | No |
| Restore | 2-3 hours | No |
| Validation | 1-2 hours | No |
| **Cutover** | 30 min - 4 hours | **Yes** |

## SQL Commands

After running the scripts, execute the generated SQL commands:

1. **On source database** - Initiate backup:
```sql
EXEC msdb.dbo.rds_backup_database 
    @source_db_name='frost-db-prd',
    @s3_arn_to_backup_to='arn:aws:s3:::bucket/backup.bak',
    @type='FULL',
    @compression='GZIP';
```

2. **Monitor progress**:
```sql
EXEC msdb.dbo.rds_task_status;
```

3. **On new instance** - Restore:
```sql
EXEC msdb.dbo.rds_restore_database 
    @restore_db_name='frost-db-prd',
    @s3_arn_to_restore_from='arn:aws:s3:::bucket/backup.bak';
```

## Rollback Plan

1. Keep source instance running for 48+ hours
2. Take final snapshot before deletion
3. Update connection strings back to source if needed

## Support

Logs are saved to `scripts/logs/` directory with timestamps.
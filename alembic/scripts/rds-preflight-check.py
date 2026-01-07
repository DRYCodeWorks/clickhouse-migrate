#!/usr/bin/env python3
"""
RDS Migration Pre-flight Validation Script
Comprehensive checks before starting migration
"""

import argparse
import boto3
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging
from botocore.exceptions import ClientError
from tabulate import tabulate

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PreflightChecker:
    def __init__(self, profile: str = 'FrostAdmin'):
        """Initialize preflight checker with AWS session."""
        self.session = boto3.Session(profile_name=profile)
        self.rds = self.session.client('rds')
        self.s3 = self.session.client('s3')
        self.iam = self.session.client('iam')
        self.cloudwatch = self.session.client('cloudwatch')
        self.account_id = self.session.client('sts').get_caller_identity()['Account']
        self.region = self.session.region_name
        
        self.checks_passed = []
        self.checks_failed = []
        self.checks_warning = []
        
    def check_instance_exists(self, instance_id: str) -> Tuple[bool, Dict]:
        """Check if RDS instance exists and get details."""
        try:
            response = self.rds.describe_db_instances(DBInstanceIdentifier=instance_id)
            instance = response['DBInstances'][0]
            
            details = {
                'instance_id': instance['DBInstanceIdentifier'],
                'status': instance['DBInstanceStatus'],
                'engine': f"{instance['Engine']} {instance['EngineVersion']}",
                'class': instance['DBInstanceClass'],
                'storage': f"{instance['AllocatedStorage']}GB ({instance.get('StorageType', 'standard')})",
                'multi_az': instance['MultiAZ'],
                'backup_retention': instance['BackupRetentionPeriod'],
                'encrypted': instance.get('StorageEncrypted', False)
            }
            
            return (True, details)
            
        except ClientError:
            return (False, {'error': f'Instance {instance_id} not found'})
    
    def check_backup_option_enabled(self, instance_id: str) -> Tuple[bool, str]:
        """Check if SQLSERVER_BACKUP_RESTORE option is enabled."""
        try:
            response = self.rds.describe_db_instances(DBInstanceIdentifier=instance_id)
            instance = response['DBInstances'][0]
            
            option_groups = instance.get('OptionGroupMemberships', [])
            if not option_groups:
                return (False, "No option group associated")
            
            option_group_name = option_groups[0]['OptionGroupName']
            og_response = self.rds.describe_option_groups(OptionGroupName=option_group_name)
            options = og_response['OptionGroupsList'][0].get('Options', [])
            
            for option in options:
                if option['OptionName'] == 'SQLSERVER_BACKUP_RESTORE':
                    iam_role = None
                    for setting in option.get('OptionSettings', []):
                        if setting['Name'] == 'IAM_ROLE_ARN':
                            iam_role = setting['Value']
                    
                    if iam_role:
                        return (True, f"Enabled with IAM role: {iam_role.split('/')[-1]}")
                    else:
                        return (False, "Option enabled but no IAM role configured")
            
            return (False, "SQLSERVER_BACKUP_RESTORE option not enabled")
            
        except Exception as e:
            return (False, f"Error checking option group: {str(e)}")
    
    def check_s3_bucket(self, bucket_name: str) -> Tuple[bool, Dict]:
        """Check S3 bucket exists and permissions."""
        try:
            # Check bucket exists
            self.s3.head_bucket(Bucket=bucket_name)
            
            # Check versioning
            versioning = self.s3.get_bucket_versioning(Bucket=bucket_name)
            versioning_enabled = versioning.get('Status') == 'Enabled'
            
            # Check lifecycle rules
            try:
                lifecycle = self.s3.get_bucket_lifecycle_configuration(Bucket=bucket_name)
                lifecycle_rules = len(lifecycle.get('Rules', []))
            except ClientError:
                lifecycle_rules = 0
            
            # Check bucket size
            try:
                response = self.s3.list_objects_v2(Bucket=bucket_name)
                total_size = sum(obj['Size'] for obj in response.get('Contents', []))
                object_count = response.get('KeyCount', 0)
            except:
                total_size = 0
                object_count = 0
            
            details = {
                'versioning': 'Enabled' if versioning_enabled else 'Disabled',
                'lifecycle_rules': lifecycle_rules,
                'object_count': object_count,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
            
            return (True, details)
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                return (False, {'error': 'Bucket does not exist'})
            elif e.response['Error']['Code'] == 'Forbidden':
                return (False, {'error': 'Access denied to bucket'})
            else:
                return (False, {'error': str(e)})
    
    def check_iam_role(self, role_name: str = 'rds-s3-backup-restore-role') -> Tuple[bool, Dict]:
        """Check if IAM role exists with correct permissions."""
        try:
            # Check role exists
            response = self.iam.get_role(RoleName=role_name)
            role = response['Role']
            
            # Check trust policy
            trust_policy = role['AssumeRolePolicyDocument']
            rds_trusted = False
            for statement in trust_policy.get('Statement', []):
                if 'rds.amazonaws.com' in str(statement.get('Principal', {})):
                    rds_trusted = True
                    break
            
            # Check attached policies
            policies = self.iam.list_role_policies(RoleName=role_name)
            policy_names = policies.get('PolicyNames', [])
            
            details = {
                'role_arn': role['Arn'],
                'rds_trust': 'Yes' if rds_trusted else 'No',
                'policies': len(policy_names)
            }
            
            return (True, details)
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchEntity':
                return (False, {'error': 'IAM role not found'})
            else:
                return (False, {'error': str(e)})
    
    def check_storage_metrics(self, instance_id: str) -> Tuple[bool, Dict]:
        """Check storage utilization and growth trends."""
        try:
            response = self.rds.describe_db_instances(DBInstanceIdentifier=instance_id)
            instance = response['DBInstances'][0]
            allocated_storage = instance['AllocatedStorage']
            
            # Get free storage space from CloudWatch
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=1)
            
            metrics = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/RDS',
                MetricName='FreeStorageSpace',
                Dimensions=[
                    {'Name': 'DBInstanceIdentifier', 'Value': instance_id}
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average']
            )
            
            if metrics['Datapoints']:
                latest_free_bytes = sorted(metrics['Datapoints'], 
                                         key=lambda x: x['Timestamp'])[-1]['Average']
                free_gb = latest_free_bytes / (1024**3)
                used_gb = allocated_storage - free_gb
                utilization_pct = (used_gb / allocated_storage) * 100
                
                details = {
                    'allocated_gb': allocated_storage,
                    'used_gb': round(used_gb, 2),
                    'free_gb': round(free_gb, 2),
                    'utilization_pct': round(utilization_pct, 2),
                    'estimated_backup_gb': round(used_gb * 0.2, 2)  # Rough compression estimate
                }
                
                status = True
                if utilization_pct < 10:
                    self.checks_warning.append(f"Very low storage utilization ({utilization_pct:.1f}%)")
                
                return (status, details)
            else:
                return (False, {'error': 'No CloudWatch metrics available'})
                
        except Exception as e:
            return (False, {'error': str(e)})
    
    def check_backup_window(self, instance_id: str) -> Tuple[bool, Dict]:
        """Check backup window and recent backup status."""
        try:
            response = self.rds.describe_db_instances(DBInstanceIdentifier=instance_id)
            instance = response['DBInstances'][0]
            
            details = {
                'backup_window': instance.get('PreferredBackupWindow', 'Not set'),
                'backup_retention': f"{instance['BackupRetentionPeriod']} days",
                'latest_restorable': instance.get('LatestRestorableTime', 'N/A').strftime('%Y-%m-%d %H:%M:%S') 
                    if instance.get('LatestRestorableTime') else 'N/A'
            }
            
            # Check recent snapshots
            snapshots = self.rds.describe_db_snapshots(
                DBInstanceIdentifier=instance_id,
                SnapshotType='automated'
            )
            
            if snapshots['DBSnapshots']:
                latest_snapshot = sorted(snapshots['DBSnapshots'], 
                                       key=lambda x: x['SnapshotCreateTime'])[-1]
                details['latest_snapshot'] = latest_snapshot['SnapshotCreateTime'].strftime('%Y-%m-%d %H:%M:%S')
                details['snapshot_count'] = len(snapshots['DBSnapshots'])
            else:
                details['latest_snapshot'] = 'No automated snapshots'
                details['snapshot_count'] = 0
            
            return (True, details)
            
        except Exception as e:
            return (False, {'error': str(e)})
    
    def estimate_migration_time(self, instance_id: str, database_size_gb: float) -> Dict:
        """Estimate migration time based on instance type and database size."""
        try:
            response = self.rds.describe_db_instances(DBInstanceIdentifier=instance_id)
            instance = response['DBInstances'][0]
            instance_class = instance['DBInstanceClass']
            
            # Rough estimates based on instance class (MB/s)
            throughput_estimates = {
                'db.t3': 50,     # Burstable
                'db.m5': 100,    # General purpose
                'db.m6i': 150,   # General purpose (newer)
                'db.r5': 200,    # Memory optimized
                'db.r6i': 250,   # Memory optimized (newer)
            }
            
            # Get instance family
            family = '.'.join(instance_class.split('.')[:2])
            throughput_mbps = throughput_estimates.get(family, 75)  # Default estimate
            
            # Calculate times (with compression factor)
            compressed_size_gb = database_size_gb * 0.2  # Assume 5:1 compression
            backup_time_min = (compressed_size_gb * 1024) / (throughput_mbps * 60)
            restore_time_min = backup_time_min * 1.5  # Restore usually slower
            
            return {
                'instance_class': instance_class,
                'estimated_backup_size_gb': round(compressed_size_gb, 2),
                'estimated_backup_time_min': round(backup_time_min, 0),
                'estimated_restore_time_min': round(restore_time_min, 0),
                'total_migration_time_min': round(backup_time_min + restore_time_min + 60, 0)  # +60 for overhead
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def run_all_checks(self, config: Dict) -> bool:
        """Run all preflight checks."""
        print("\n" + "=" * 80)
        print("RDS MIGRATION PREFLIGHT CHECKS")
        print("=" * 80)
        print(f"Environment: {config['environment']}")
        print(f"Source Instance: {config['source_instance']}")
        print(f"Target Instance: {config.get('target_instance', 'Not specified')}")
        print(f"S3 Bucket: {config['s3_bucket']}")
        print("=" * 80 + "\n")
        
        all_checks = []
        
        # 1. Check source instance
        print("1. Checking source instance...")
        exists, details = self.check_instance_exists(config['source_instance'])
        if exists:
            all_checks.append(('Source Instance', '✅ PASS', f"Status: {details['status']}"))
            self.checks_passed.append('Source instance exists')
            
            # Display instance details
            print(f"   Instance Details:")
            for key, value in details.items():
                if key != 'error':
                    print(f"     {key}: {value}")
        else:
            all_checks.append(('Source Instance', '❌ FAIL', details.get('error', 'Unknown error')))
            self.checks_failed.append('Source instance not found')
        
        # 2. Check backup option
        print("\n2. Checking backup/restore option...")
        enabled, message = self.check_backup_option_enabled(config['source_instance'])
        if enabled:
            all_checks.append(('Backup Option', '✅ PASS', message))
            self.checks_passed.append('Backup option enabled')
        else:
            all_checks.append(('Backup Option', '❌ FAIL', message))
            self.checks_failed.append(f'Backup option: {message}')
        
        # 3. Check S3 bucket
        print("\n3. Checking S3 bucket...")
        exists, details = self.check_s3_bucket(config['s3_bucket'])
        if exists:
            if details.get('versioning') != 'Enabled':
                all_checks.append(('S3 Bucket', '⚠️ WARN', 'Bucket exists but versioning disabled'))
                self.checks_warning.append('S3 versioning not enabled')
            else:
                all_checks.append(('S3 Bucket', '✅ PASS', f"Objects: {details['object_count']}, Size: {details['total_size_mb']}MB"))
                self.checks_passed.append('S3 bucket configured')
        else:
            all_checks.append(('S3 Bucket', '❌ FAIL', details.get('error', 'Unknown error')))
            self.checks_failed.append(f"S3 bucket: {details.get('error')}")
        
        # 4. Check IAM role
        print("\n4. Checking IAM role...")
        exists, details = self.check_iam_role()
        if exists:
            if details.get('rds_trust') == 'Yes':
                all_checks.append(('IAM Role', '✅ PASS', f"Policies: {details['policies']}"))
                self.checks_passed.append('IAM role configured')
            else:
                all_checks.append(('IAM Role', '⚠️ WARN', 'Role exists but RDS trust not configured'))
                self.checks_warning.append('IAM role trust policy issue')
        else:
            all_checks.append(('IAM Role', '❌ FAIL', details.get('error', 'Unknown error')))
            self.checks_failed.append(f"IAM role: {details.get('error')}")
        
        # 5. Check storage metrics
        print("\n5. Checking storage utilization...")
        success, details = self.check_storage_metrics(config['source_instance'])
        if success:
            all_checks.append(('Storage', '✅ PASS', 
                             f"Used: {details['used_gb']}GB/{details['allocated_gb']}GB ({details['utilization_pct']}%)"))
            self.checks_passed.append('Storage metrics available')
            
            # Estimate migration time
            estimates = self.estimate_migration_time(config['source_instance'], details['used_gb'])
            print(f"\n   Migration Time Estimates:")
            print(f"     Backup: ~{estimates['estimated_backup_time_min']} minutes")
            print(f"     Restore: ~{estimates['estimated_restore_time_min']} minutes")
            print(f"     Total: ~{estimates['total_migration_time_min']} minutes")
        else:
            all_checks.append(('Storage', '⚠️ WARN', 'CloudWatch metrics not available'))
            self.checks_warning.append('Storage metrics unavailable')
        
        # 6. Check backup configuration
        print("\n6. Checking backup configuration...")
        success, details = self.check_backup_window(config['source_instance'])
        if success:
            all_checks.append(('Backups', '✅ PASS', 
                             f"Retention: {details['backup_retention']}, Latest: {details.get('latest_snapshot', 'N/A')}"))
            self.checks_passed.append('Backup configuration OK')
        else:
            all_checks.append(('Backups', '⚠️ WARN', 'Unable to check backup status'))
            self.checks_warning.append('Backup status unknown')
        
        # Display summary
        print("\n" + "=" * 80)
        print("PREFLIGHT CHECK SUMMARY")
        print("=" * 80)
        print(tabulate(all_checks, headers=['Check', 'Status', 'Details'], tablefmt='grid'))
        
        # Overall status
        print(f"\n✅ Passed: {len(self.checks_passed)}")
        print(f"⚠️  Warnings: {len(self.checks_warning)}")
        print(f"❌ Failed: {len(self.checks_failed)}")
        
        if self.checks_failed:
            print("\n❌ PREFLIGHT CHECKS FAILED")
            print("Failed checks must be resolved before migration:")
            for check in self.checks_failed:
                print(f"  - {check}")
            return False
        elif self.checks_warning:
            print("\n⚠️  PREFLIGHT CHECKS PASSED WITH WARNINGS")
            print("Warnings (review but can proceed):")
            for check in self.checks_warning:
                print(f"  - {check}")
            return True
        else:
            print("\n✅ ALL PREFLIGHT CHECKS PASSED")
            print("Ready to proceed with migration!")
            return True


def main():
    parser = argparse.ArgumentParser(description='RDS Migration Preflight Checks')
    parser.add_argument('--source-instance', required=True, help='Source RDS instance')
    parser.add_argument('--target-instance', help='Target RDS instance (if exists)')
    parser.add_argument('--s3-bucket', required=True, help='S3 bucket for backups')
    parser.add_argument('--environment', choices=['dev', 'stg', 'prd'], default='dev',
                       help='Environment')
    parser.add_argument('--profile', default='FrostAdmin',
                       help='AWS profile to use')
    
    args = parser.parse_args()
    
    # Configuration
    config = {
        'source_instance': args.source_instance,
        'target_instance': args.target_instance,
        's3_bucket': args.s3_bucket,
        'environment': args.environment
    }
    
    # Run checks
    checker = PreflightChecker(profile=args.profile)
    success = checker.run_all_checks(config)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
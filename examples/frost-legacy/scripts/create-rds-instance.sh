#!/bin/bash
# create-rds-instance.sh - Create new RDS instance with Secrets Manager integration
# This script copies configuration from an existing instance and creates a new smaller one

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
warn() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
info() { echo -e "${BLUE}[INFO]${NC} $1"; }

# Function to prompt for user confirmation
confirm() {
    if [[ "$AUTO_APPROVE" == "true" ]]; then
        info "AUTO-APPROVE: $1"
        return 0
    fi
    echo
    echo -e "${YELLOW}$1${NC}"
    read -p "Do you want to continue? (yes/no): " -r
    echo
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log "Operation cancelled by user"
        exit 0
    fi
}

# Function to pause and wait for user
pause() {
    echo
    echo -e "${BLUE}$1${NC}"
    read -p "Press ENTER to continue or Ctrl+C to abort..."
    echo
}

# Configuration variables - MODIFY THESE AS NEEDED
NEW_INSTANCE_NAME="${1:-tf-frost-db-dev2}"  # Can pass as first argument
CURRENT_INSTANCE_NAME="${2:-tf-frost-db-dev}"  # Can pass as second argument
ALLOCATED_STORAGE="${3:-50}"  # Can pass as third argument
MAX_ALLOCATED_STORAGE="${4:-100}"  # Can pass as fourth argument
PUBLICLY_ACCESSIBLE="${5:-true}"  # Set to "false" for private access only
AUTO_APPROVE="${6:-false}"  # Set to "true" to skip all prompts

# Validate required tools
command -v aws >/dev/null 2>&1 || error "AWS CLI is required but not installed"
command -v jq >/dev/null 2>&1 || error "jq is required but not installed"

# Display configuration
log "RDS Instance Creation Configuration:"
info "  Source Instance: $CURRENT_INSTANCE_NAME"
info "  New Instance: $NEW_INSTANCE_NAME"
info "  Initial Storage: ${ALLOCATED_STORAGE}GB"
info "  Max Storage: ${MAX_ALLOCATED_STORAGE}GB"
info "  Publicly Accessible: ${PUBLICLY_ACCESSIBLE}"
info "  Auto-Approve Mode: ${AUTO_APPROVE}"
info "  Password Management: RDS Managed (automatic)"

# BREAKPOINT 1: Confirm configuration
confirm "⚠️  Please review the configuration above. This will create a new RDS instance and may incur AWS charges."

# Step 1: Get current instance details to copy configuration
log "Getting current instance configuration..."
if ! CURRENT_CONFIG=$(aws rds describe-db-instances \
    --db-instance-identifier $CURRENT_INSTANCE_NAME \
    --query 'DBInstances[0]' \
    --output json 2>/dev/null); then
    error "Failed to get configuration for instance: $CURRENT_INSTANCE_NAME"
fi

# Extract values from current instance
VPC_SECURITY_GROUPS=$(echo $CURRENT_CONFIG | jq -r '.VpcSecurityGroups[].VpcSecurityGroupId' | tr '\n' ' ')
DB_SUBNET_GROUP=$(echo $CURRENT_CONFIG | jq -r '.DBSubnetGroup.DBSubnetGroupName')
KMS_KEY_ID=$(echo $CURRENT_CONFIG | jq -r '.KmsKeyId // empty')
PARAMETER_GROUP=$(echo $CURRENT_CONFIG | jq -r '.DBParameterGroups[0].DBParameterGroupName // empty')
ENGINE_VERSION=$(echo $CURRENT_CONFIG | jq -r '.EngineVersion')
AVAILABILITY_ZONE=$(echo $CURRENT_CONFIG | jq -r '.AvailabilityZone // empty')
ENGINE=$(echo $CURRENT_CONFIG | jq -r '.Engine')

# Validate extracted values
[ -z "$VPC_SECURITY_GROUPS" ] && error "Could not extract VPC Security Groups"
[ -z "$DB_SUBNET_GROUP" ] && error "Could not extract DB Subnet Group"
[ -z "$ENGINE_VERSION" ] && error "Could not extract Engine Version"

info "Current instance configuration extracted:"
info "  VPC Security Groups: $VPC_SECURITY_GROUPS"
info "  DB Subnet Group: $DB_SUBNET_GROUP"  
info "  KMS Key ID: ${KMS_KEY_ID:-'(none)'}"
info "  Parameter Group: ${PARAMETER_GROUP:-'(default)'}"
info "  Engine: $ENGINE"
info "  Engine Version: $ENGINE_VERSION"
info "  Availability Zone: ${AVAILABILITY_ZONE:-'(auto)'}"

# BREAKPOINT 2: Confirm extracted configuration
confirm "⚠️  Please verify the extracted configuration above matches your source instance settings."

# BREAKPOINT 3: Final confirmation before creating instance
confirm "🚨 FINAL CONFIRMATION: About to create RDS instance '$NEW_INSTANCE_NAME'. This cannot be easily undone and will incur ongoing AWS charges."

# Step 2: Check if instance already exists
log "Checking if instance already exists..."
if aws rds describe-db-instances --db-instance-identifier $NEW_INSTANCE_NAME >/dev/null 2>&1; then
    error "Instance $NEW_INSTANCE_NAME already exists. Please choose a different name or delete the existing instance."
fi

# Step 3: Build the create-db-instance command
log "Creating new RDS instance..."
info "This will take several minutes..."

# Build the base command with properly quoted parameters
info "Executing create-db-instance command..."

# Create the instance with properly formatted parameters
if aws rds create-db-instance \
    --db-instance-identifier "$NEW_INSTANCE_NAME" \
    --allocated-storage "$ALLOCATED_STORAGE" \
    --max-allocated-storage "$MAX_ALLOCATED_STORAGE" \
    --storage-type "gp3" \
    --iops 12000 \
    --storage-throughput 500 \
    --db-instance-class "db.m6i.4xlarge" \
    --engine "$ENGINE" \
    --engine-version "$ENGINE_VERSION" \
    --master-username "admin" \
    --manage-master-user-password \
    --vpc-security-group-ids $VPC_SECURITY_GROUPS \
    --db-subnet-group-name "$DB_SUBNET_GROUP" \
    --option-group-name "sql-server-backup-restore" \
    $([ "$PUBLICLY_ACCESSIBLE" = "true" ] && echo "--publicly-accessible" || echo "--no-publicly-accessible") \
    --backup-retention-period 7 \
    --preferred-backup-window "03:00-04:00" \
    --preferred-maintenance-window "sun:04:00-sun:05:00" \
    --storage-encrypted \
    --copy-tags-to-snapshot \
    --deletion-protection \
    --enable-performance-insights \
    --performance-insights-retention-period 7 \
    --monitoring-interval 60 \
    --enable-cloudwatch-logs-exports "error" "agent" \
    --tags "Key=Environment,Value=dev" "Key=Purpose,Value=migration" "Key=AutoShutdown,Value=false" "Key=CreatedBy,Value=migration-script" \
    $([ -n "$PARAMETER_GROUP" ] && echo "--db-parameter-group-name $PARAMETER_GROUP") \
    $([ -n "$KMS_KEY_ID" ] && [ "$KMS_KEY_ID" != "alias/aws/rds" ] && echo "--kms-key-id $KMS_KEY_ID --performance-insights-kms-key-id $KMS_KEY_ID") \
    $(aws iam get-role --role-name rds-monitoring-role >/dev/null 2>&1 && echo "--monitoring-role-arn arn:aws:iam::$(aws sts get-caller-identity --query Account --output text):role/rds-monitoring-role") \
    >/dev/null; then
    log "Instance creation initiated successfully!"
else
    error "Failed to create RDS instance"
fi

echo
log "Waiting for instance to become available..."
info "This typically takes 10-15 minutes for SQL Server instances"

# BREAKPOINT 4: Option to skip waiting
if [[ "$AUTO_APPROVE" != "true" ]]; then
    echo
    echo -e "${YELLOW}The instance is now being created. You can:${NC}"
    echo "1. Wait here for completion (recommended)"  
    echo "2. Skip waiting and check status later with: aws rds describe-db-instances --db-instance-identifier $NEW_INSTANCE_NAME"
    echo
    read -p "Wait for instance to become available? (yes/no): " -r
    echo

    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log "Skipping wait. Instance creation will continue in the background."
        log "Check status with: aws rds describe-db-instances --db-instance-identifier $NEW_INSTANCE_NAME"
        exit 0
    fi
else
    info "AUTO-APPROVE: Waiting for instance to become available..."
fi

# Wait for instance to be available with progress indication
WAIT_COUNT=0
while true; do
    STATUS=$(aws rds describe-db-instances \
        --db-instance-identifier $NEW_INSTANCE_NAME \
        --query 'DBInstances[0].DBInstanceStatus' \
        --output text 2>/dev/null)
    
    if [ "$STATUS" = "available" ]; then
        log "Instance is now available!"
        break
    elif [ "$STATUS" = "failed" ]; then
        error "Instance creation failed"
    else
        WAIT_COUNT=$((WAIT_COUNT + 1))
        info "Status: $STATUS (waited ${WAIT_COUNT} minutes)"
        sleep 60
    fi
done

# Get final instance details
log "Getting new instance details..."
INSTANCE_DETAILS=$(aws rds describe-db-instances \
    --db-instance-identifier $NEW_INSTANCE_NAME \
    --query 'DBInstances[0]' \
    --output json)

NEW_ENDPOINT=$(echo $INSTANCE_DETAILS | jq -r '.Endpoint.Address')
NEW_PORT=$(echo $INSTANCE_DETAILS | jq -r '.Endpoint.Port')
SECRET_ARN=$(echo $INSTANCE_DETAILS | jq -r '.MasterUserSecret.SecretArn // "N/A"')

echo
log "=== INSTANCE CREATION COMPLETED ==="
info "Instance ID: $NEW_INSTANCE_NAME"
info "Endpoint: $NEW_ENDPOINT:$NEW_PORT"
info "Master Password Secret ARN: $SECRET_ARN"
info "Storage: ${ALLOCATED_STORAGE}GB (auto-scaling to ${MAX_ALLOCATED_STORAGE}GB)"
echo
log "You can now proceed with the database restore process."
log "Master password is automatically managed by RDS and stored in Secrets Manager."
if [ "$SECRET_ARN" != "N/A" ]; then
    log "Retrieve password with: aws secretsmanager get-secret-value --secret-id '$SECRET_ARN'"
fi
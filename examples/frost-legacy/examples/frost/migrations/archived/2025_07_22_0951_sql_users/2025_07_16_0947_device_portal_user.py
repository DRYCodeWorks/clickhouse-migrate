"""device-portal-user

Revision ID: 97e3b48cf30b
Revises: 155ff6de6313
Create Date: 2025-07-16 09:47:10.920207

"""

import json
import secrets

import boto3
import sqlalchemy as sa
from alembic import context, op

from helpers.utils import read_sql_file

# revision identifiers, used by Alembic.
revision = "97e3b48cf30b"
down_revision = "155ff6de6313"
branch_labels = None
depends_on = None
sm = boto3.client("secretsmanager", region_name="us-east-2")

proxies = {
    "dev": "frost-dev.proxy-cmlckfm3bqu2.us-east-2.rds.amazonaws.com",
    "stg": "frost-stg.proxy-cmlckfm3bqu2.us-east-2.rds.amazonaws.com",
    "prod": "frost-prod.proxy-cmlckfm3bqu2.us-east-2.rds.amazonaws.com",
}

db_identifiers = {
    "dev": "tf-frost-db-dev",
    "stg": "tf-frost-db-stg",
    "prod": "frost-db-prd",
}


def upgrade() -> None:
    password = secrets.token_urlsafe(24)
    env = context.config.cmd_opts.name
    secret = {
        "username": "device_portal_api_login",
        "password": password,
        "engine": "sqlserver",
        "host": proxies[env],
        "port": 1433,
        "dbInstanceIdentifier": "tf-frost-db-dev",
    }
    try:
        sm.create_secret(
            Name=f"{env}/mssql/device-portal-api",
            SecretString=json.dumps(secret),
            Description="Password for the device portal API user",
        )
    except sm.exceptions.ResourceExistsException:
        sm.update_secret(
            SecretId=f"{env}/mssql/device-portal-api",
            SecretString=json.dumps(secret),
        )
    op.execute(
        read_sql_file("users/CreateDevicePortalRole").replace("?", f"'{password}'")
    )


def downgrade() -> None:
    env = context.config.cmd_opts.name
    sm.delete_secret(
        SecretId=f"{env}/mssql/device-portal-api",
        ForceDeleteWithoutRecovery=True,
    )
    op.execute("ALTER ROLE frost_api_role DROP MEMBER device_portal_api")
    op.execute("DROP USER device_portal_api")
    op.execute("DROP LOGIN device_portal_api_login")
    op.execute("DROP ROLE frost_api_role")

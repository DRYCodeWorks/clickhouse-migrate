"""alerts_handler_user

Revision ID: b83a369c3353
Revises: 04bcd602ec29
Create Date: 2025-07-16 18:50:41.920555

"""

import json
from alembic import context, op
from helpers.utils import read_sql_file
import sqlalchemy as sa
import boto3
import secrets


# revision identifiers, used by Alembic.
revision = "b83a369c3353"
down_revision = "04bcd602ec29"
branch_labels = None
depends_on = None

role_name = "frost_alerts_role"
user_login = "alerts_handler_login"
user_name = "alerts_handler"
secret_name = "alerts-handler"

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
        "username": user_login,
        "password": password,
        "engine": "sqlserver",
        "host": proxies[env],
        "port": 1433,
        "dbInstanceIdentifier": "tf-frost-db-dev",
    }
    try:
        sm.create_secret(
            Name=f"{env}/mssql/{secret_name}",
            SecretString=json.dumps(secret),
            Description="Password for the device portal API user",
        )
    except sm.exceptions.ResourceExistsException:
        sm.update_secret(
            SecretId=f"{env}/mssql/{secret_name}",
            SecretString=json.dumps(secret),
        )
    op.execute(
        read_sql_file("users/CreateAlertEngineRole").replace("?", f"'{password}'")
    )


def downgrade() -> None:
    env = context.config.cmd_opts.name
    sm.delete_secret(
        SecretId=f"{env}/mssql/{secret_name}",
        ForceDeleteWithoutRecovery=True,
    )
    op.execute(f"ALTER ROLE {role_name} DROP MEMBER {user_name}")
    op.execute(f"DROP USER {user_name}")
    op.execute(f"DROP LOGIN {user_login}")
    op.execute(f"DROP ROLE {role_name}")

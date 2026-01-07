"""particle_handler_user

Revision ID: accaf6a42929
Revises: 97e3b48cf30b
Create Date: 2025-07-16 16:24:40.689340

"""

import json
from alembic import context, op
from helpers.utils import read_sql_file
import sqlalchemy as sa
import boto3
import secrets


# revision identifiers, used by Alembic.
revision = "accaf6a42929"
down_revision = "97e3b48cf30b"
branch_labels = None
depends_on = None

role_name = "frost_particle_role"
user_login = "particle_handler_login"
user_name = "particle_handler"
secret_name = "particle-handler"

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
    op.execute(read_sql_file("users/CreateParticleRole").replace("?", f"'{password}'"))


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

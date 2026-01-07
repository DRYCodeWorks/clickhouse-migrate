"""devices_dict

Revision ID: 1b7c9aeb0bf9
Revises: f436c220f48c
Create Date: 2025-08-15 15:40:43.685672

"""

from alembic import context, op
import sqlalchemy as sa
from helpers.utils import read_sql_file
import boto3

# revision identifiers, used by Alembic.
revision = "1b7c9aeb0bf9"
down_revision = "f436c220f48c"
branch_labels = None
depends_on = None

ssm = boto3.client("ssm")

api_gw_env_mappings = {
    "dev": "https://dpa-dev.frosttech.io",
    "stg": "https://dpa-stg.frosttech.io",
    "prod": "https://app-api.frosttech.io",
}


def upgrade() -> None:
    env = context.config.cmd_opts.name
    env_name = env.lower().split("_")[1]
    api_gw_url = api_gw_env_mappings[env_name]
    clickhouse_api_key = ssm.get_parameter(
        Name=f"/{env_name}/clickhouse-api-key", WithDecryption=True
    )["Parameter"]["Value"]

    op.execute(
        read_sql_file("CreateDevicesDict", clickhouse=True)
        .replace("@api_key", clickhouse_api_key)
        .replace("@dpa_url", api_gw_url)
    )


def downgrade() -> None:
    op.execute("DROP DICTIONARY devices")

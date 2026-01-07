"""
This is the primary entrypoint for alembic. The ini file is automatically loaded into context,
and values stored there can be queried on the alembic.context object.
"""

import json
import os
from logging.config import fileConfig
from urllib.parse import quote

import boto3
from alembic import context
from alembic.ddl import impl
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

from schemas import get_metadata

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
load_dotenv()
# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = get_metadata(config.cmd_opts.name)

section = config.config_ini_section

sm = boto3.client("secretsmanager")


class ClickhouseImpl(impl.DefaultImpl):
    """
    Implementation of Alembic migration behavior for Clickhouse DB
    """

    __dialect__ = "clickhouse"
    transactional_ddl = False


def gen_mapping(env):
    return {
        f"{env.upper()}_{arg}": os.environ[f"{env.upper()}_{arg}"]
        for arg in [
            "HOST",
            "DATABASE",
            "SECRET",
        ]
    }


for key, val in gen_mapping(config.cmd_opts.name).items():
    if "SECRET" in key:
        response = json.loads(sm.get_secret_value(SecretId=val)["SecretString"])
        STAGE = config.cmd_opts.name.upper()
        for k, v in {
            x: y for x, y in response.items() if x in ("username", "password")
        }.items():
            if k.lower() == "password":
                v = quote(v)
                v = v.replace("%", "%%")
            config.set_section_option(section, f"{STAGE}_{k.upper()}", v)

    config.set_section_option(section, key, val)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

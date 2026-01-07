"""
This is the primary entrypoint for alembic. The ini file is automatically loaded into context,
and values stored there can be queried on the alembic.context object.

This version has been generalized to work with configurable credential systems
instead of being hardcoded to AWS/Frost infrastructure.
"""

import os
import sys
from logging.config import fileConfig
from urllib.parse import quote
from pathlib import Path

from alembic import context
from alembic.ddl import impl
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

# Try to import the configuration manager if available
try:
    from config.manager import ConfigManager
    CONFIG_MANAGER_AVAILABLE = True
except ImportError:
    CONFIG_MANAGER_AVAILABLE = False

# Import schema metadata
try:
    from schemas import get_metadata
except ImportError:
    # Fallback for simple setups
    def get_metadata(env):
        from schemas.schema import Base
        return Base.metadata

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
target_metadata = get_metadata(config.cmd_opts.name if config.cmd_opts else 'local')

section = config.config_ini_section


class ClickhouseImpl(impl.DefaultImpl):
    """
    Implementation of Alembic migration behavior for Clickhouse DB
    """

    __dialect__ = "clickhouse"
    transactional_ddl = False


def setup_environment_variables():
    """
    Setup environment variables for the current environment.
    
    This function handles credential loading through the new configurable system
    if available, or falls back to simple environment variable patterns.
    """
    env_name = config.cmd_opts.name if config.cmd_opts else 'local'
    
    # Try to use the new configuration manager system
    if CONFIG_MANAGER_AVAILABLE:
        try:
            config_path = Path.cwd() / "config" / "config.yaml"
            if config_path.exists():
                manager = ConfigManager(config_path)
                env_config = manager.get_environment_config(env_name)
                
                # Set environment variables for alembic.ini interpolation
                env_upper = env_name.upper()
                
                # Map configuration to environment variables
                if 'host' in env_config:
                    os.environ[f"{env_upper}_HOST"] = env_config['host']
                if 'port' in env_config:
                    os.environ[f"{env_upper}_PORT"] = str(env_config['port'])
                if 'database' in env_config:
                    os.environ[f"{env_upper}_DATABASE"] = env_config['database']
                if 'username' in env_config:
                    os.environ[f"{env_upper}_USERNAME"] = env_config['username']
                if 'password' in env_config:
                    # Handle password encoding for URL
                    password = env_config['password']
                    if '%' in password:
                        password = quote(password).replace('%', '%%')
                    os.environ[f"{env_upper}_PASSWORD"] = password
                
                # Handle protocol parameters
                protocol = env_config.get('protocol', 'http')
                protocol_params = f"?protocol={protocol}" if protocol == 'https' else ""
                os.environ[f"{env_upper}_PROTOCOL_PARAMS"] = protocol_params
                
                return True
        except Exception as e:
            print(f"Warning: Could not load configuration for {env_name}: {str(e)}")
            print("Falling back to environment variable patterns...")
    
    # Fallback: Ensure basic environment variables exist with defaults
    env_upper = env_name.upper()
    defaults = {
        f"{env_upper}_HOST": "localhost",
        f"{env_upper}_PORT": "8123", 
        f"{env_upper}_DATABASE": "default",
        f"{env_upper}_USERNAME": "",
        f"{env_upper}_PASSWORD": "",
        f"{env_upper}_PROTOCOL_PARAMS": ""
    }
    
    for key, default_value in defaults.items():
        if key not in os.environ:
            os.environ[key] = default_value
    
    return False


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Setup environment variables
    setup_environment_variables()
    
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
    # Setup environment variables  
    setup_environment_variables()
    
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
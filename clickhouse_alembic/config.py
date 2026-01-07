"""Configuration loading for clickhouse-alembic."""

import os
from pathlib import Path
from typing import Any

import yaml


def load_config(config_path: Path) -> dict[str, Any]:
    """
    Load YAML configuration file.

    Args:
        config_path: Path to config.yaml

    Returns:
        Parsed configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path) as f:
        return yaml.safe_load(f)


def get_env_config(env_name: str, config_path: Path) -> dict[str, Any]:
    """
    Get configuration for a specific environment, merging defaults.

    Loads non-secret config from YAML, secrets from environment variables.

    Args:
        env_name: Environment name (dev, staging, production, etc.)
        config_path: Path to config.yaml

    Returns:
        Complete environment configuration with secrets

    Raises:
        ValueError: If environment not found or required secrets missing
    """
    config = load_config(config_path)

    environments = config.get("environments", {})
    if env_name not in environments:
        available = ", ".join(environments.keys()) or "(none)"
        raise ValueError(f"Unknown environment: {env_name}. Available: {available}")

    # Merge defaults with environment-specific config
    defaults = config.get("defaults", {})
    env_config = {**defaults, **environments[env_name]}

    # Load secrets from environment variables
    env_upper = env_name.upper()

    # Required: service password
    password_key = f"CH_{env_upper}_PASSWORD"
    password = os.environ.get(password_key)
    if not password:
        raise ValueError(
            f"{password_key} environment variable is required.\n"
            f"Set it in .env.local or your shell environment."
        )
    env_config["password"] = password

    # Optional: admin password (for bootstrap)
    admin_password_key = f"CH_{env_upper}_ADMIN_PASSWORD"
    env_config["admin_password"] = os.environ.get(admin_password_key)

    # Optional: dict_reader password (for dictionaries)
    dict_password_key = f"CH_{env_upper}_DICT_READER_PASSWORD"
    env_config["dict_reader_password"] = os.environ.get(dict_password_key)

    return env_config

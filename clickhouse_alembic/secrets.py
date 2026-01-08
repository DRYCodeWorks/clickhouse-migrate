"""Secrets management with environment variable and SSM support."""

import os
from typing import Optional


class SSMSecretNotFoundError(Exception):
    """Raised when an SSM parameter cannot be found."""

    pass


def _get_ssm_client():
    """Get boto3 SSM client, raising helpful error if boto3 not installed."""
    try:
        import boto3
    except ImportError:
        raise ImportError(
            "boto3 is required for SSM support. "
            "Install with: pip install clickhouse-alembic[ssm]"
        )
    return boto3.client("ssm")


def get_secret(
    env_name: str,
    key: str,
    *,
    ssm_path: Optional[str] = None,
    required: bool = True,
) -> Optional[str]:
    """
    Get a secret value from environment variable or SSM.

    Precedence:
    1. Environment variable CH_{ENV}_{KEY} (e.g., CH_DEV_PASSWORD)
    2. SSM parameter at ssm_path (if provided)
    3. None (if not required) or raise ValueError

    Args:
        env_name: Environment name (dev, staging, production)
        key: Secret key (password, admin_password, dict_reader_password)
        ssm_path: Optional SSM parameter path
        required: Whether to raise if secret not found

    Returns:
        Secret value or None if not required and not found

    Raises:
        ValueError: If required and not found in env or SSM
        SSMSecretNotFoundError: If SSM path provided but parameter not found
        ImportError: If SSM path provided but boto3 not installed
    """
    # Build environment variable name
    env_var = f"CH_{env_name.upper()}_{key.upper()}"

    # Check environment variable first
    value = os.environ.get(env_var)
    if value:
        return value

    # Try SSM if path provided
    if ssm_path:
        client = _get_ssm_client()
        try:
            response = client.get_parameter(Name=ssm_path, WithDecryption=True)
            return response["Parameter"]["Value"]
        except Exception as e:
            if required:
                raise SSMSecretNotFoundError(
                    f"SSM parameter not found: {ssm_path}. Error: {e}"
                )
            return None

    # Not found anywhere
    if required:
        raise ValueError(
            f"{env_var} is required. "
            f"Set it in .env.local or provide an SSM path in config.yaml."
        )

    return None

"""Secrets management with environment variable and SSM support."""

import os
from typing import Optional


class SSMSecretNotFoundError(Exception):
    """Raised when an SSM parameter cannot be found."""

    pass


def _get_ssm_client():  # type: ignore[no-untyped-def]
    """Get boto3 SSM client, raising helpful error if boto3 not installed."""
    try:
        import boto3  # type: ignore[import-not-found,import-untyped]
    except ImportError:
        raise ImportError(
            "boto3 is required for SSM support. "
            "Install with: pip install clickhouse-alembic[ssm]"
        )
    return boto3.client("ssm")


def _get_ssm_exceptions():  # type: ignore[no-untyped-def]
    """Get boto3 SSM exception classes."""
    try:
        from botocore.exceptions import ClientError  # type: ignore[import-not-found,import-untyped]

        return ClientError
    except ImportError:
        # Fallback if botocore not available (shouldn't happen if boto3 is installed)
        return Exception


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
    1. Environment variable CH_{ENV}_{KEY} (e.g., CH_DEV_MIGRATION_PASSWORD)
    2. Legacy env var for migration_password: CH_{ENV}_PASSWORD
    3. SSM parameter at ssm_path (if provided)
    4. None (if not required) or raise ValueError

    Args:
        env_name: Environment name (dev, staging, production)
        key: Secret key (migration_password, admin_password, dict_reader_password)
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

    # Legacy support: CH_{ENV}_PASSWORD for migration_password
    if key == "migration_password":
        legacy_var = f"CH_{env_name.upper()}_PASSWORD"
        value = os.environ.get(legacy_var)
        if value:
            return value

    # Try SSM if path provided
    if ssm_path:
        client = _get_ssm_client()
        ClientError = _get_ssm_exceptions()
        try:
            response = client.get_parameter(Name=ssm_path, WithDecryption=True)
            return response["Parameter"]["Value"]  # type: ignore[no-any-return]
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ParameterNotFound":
                if required:
                    raise SSMSecretNotFoundError(f"SSM parameter not found: {ssm_path}") from e
                return None
            # Re-raise other AWS errors (permission denied, etc.)
            raise

    # Not found anywhere
    if required:
        raise ValueError(
            f"{env_var} is required. "
            f"Set it in .env.local or provide an SSM path in config.yaml."
        )

    return None

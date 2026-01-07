"""
Bootstrap script for initializing ClickHouse database and users.

Usage:
    ch-migrate bootstrap <environment>

This script:
1. Connects using admin credentials
2. Creates the target database
3. Creates dict_reader user (for dictionary sources)
4. Creates service user (for migrations and application)
"""

import sys
from pathlib import Path

import clickhouse_connect

from clickhouse_alembic.config import get_env_config


def escape_sql_string(s: str) -> str:
    """Escape a string for use in SQL single quotes."""
    return s.replace("\\", "\\\\").replace("'", "''")


def get_bootstrap_sql() -> str:
    """Read the bootstrap SQL template."""
    template_path = Path(__file__).parent / "templates" / "bootstrap" / "init_users.sql"
    return template_path.read_text()


def run_bootstrap(env_name: str, config_path: Path | None = None) -> None:
    """
    Run bootstrap for the specified environment.

    Args:
        env_name: Environment name (dev, staging, production, etc.)
        config_path: Path to config.yaml (defaults to ./config.yaml)
    """
    if config_path is None:
        config_path = Path.cwd() / "config.yaml"

    print(f"==> Loading environment: {env_name}")
    env_config = get_env_config(env_name, config_path)

    # Validate admin credentials exist
    admin_password = env_config.get("admin_password")
    if not admin_password:
        env_upper = env_name.upper()
        raise ValueError(
            f"CH_{env_upper}_ADMIN_PASSWORD is required for bootstrap.\n"
            f"Set it in .env.local or your shell environment."
        )

    # Validate dict_reader password exists
    dict_reader_password = env_config.get("dict_reader_password")
    if not dict_reader_password:
        env_upper = env_name.upper()
        raise ValueError(
            f"CH_{env_upper}_DICT_READER_PASSWORD is required for bootstrap.\n"
            f"Set it in .env.local or your shell environment."
        )

    host = env_config["host"]
    admin_user = env_config.get("admin_user", "default")
    secure = env_config.get("secure", True)
    port = env_config.get("port", 8443 if secure else 8123)

    print(f"==> Connecting as admin: {admin_user}@{host}")

    # Read and populate SQL template
    sql_template = get_bootstrap_sql()
    sql = sql_template.format(
        db=env_config["database"],
        dict_reader_name=env_config.get("dict_reader_name", "dict_reader"),
        dict_reader_password=escape_sql_string(dict_reader_password),
        service_user=env_config["user"],
        service_password=escape_sql_string(env_config["password"]),
    )

    print(f"==> Creating database: {env_config['database']}")
    print(f"==> Creating user: {env_config.get('dict_reader_name', 'dict_reader')} (dict_reader)")
    print(f"==> Creating user: {env_config['user']} (service)")

    # Execute bootstrap SQL
    client = clickhouse_connect.get_client(
        host=host,
        port=port,
        username=admin_user,
        password=admin_password,
        secure=secure,
        interface="https" if secure else "http",
    )

    for statement in sql.split(";"):
        statement = statement.strip()
        if statement and not statement.startswith("--"):
            client.command(statement)

    print("==> Bootstrap complete!")
    print(f"\nYou can now run migrations:")
    print(f"  ./migrate.sh {env_name} up")


def main() -> None:
    """CLI entrypoint for bootstrap."""
    if len(sys.argv) != 2:
        print("Usage: ch-migrate bootstrap <environment>")
        print("Example: ch-migrate bootstrap dev")
        sys.exit(1)

    try:
        run_bootstrap(sys.argv[1])
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

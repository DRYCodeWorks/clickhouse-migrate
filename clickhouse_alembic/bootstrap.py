"""
Bootstrap script for initializing ClickHouse database and users.

Usage:
    ch-migrate bootstrap <environment>
    ch-migrate bootstrap <environment> --dry-run

This script:
1. Connects using admin credentials
2. Creates the target database (if not exists)
3. Creates roles for migration, read-only, and dict access
4. Creates users and assigns roles
5. Is idempotent - safe to run multiple times
"""

import sys
from pathlib import Path
from typing import Optional

import clickhouse_connect

from clickhouse_alembic.config import get_env_config
from clickhouse_alembic.secrets import get_secret


def escape_sql_string(s: str) -> str:
    """Escape a string for use in SQL single quotes."""
    return s.replace("\\", "\\\\").replace("'", "''")


def build_bootstrap_sql(
    *,
    project: str,
    db: str,
    migration_user: str,
    migration_password: str,
    dict_reader_name: Optional[str] = None,
    dict_reader_password: Optional[str] = None,
    mcp_user_name: Optional[str] = None,
    mcp_password: Optional[str] = None,
) -> str:
    """
    Build the bootstrap SQL with optional users.

    Args:
        project: Project name (used for role prefixes)
        db: Database name
        migration_user: Migration user name
        migration_password: Migration user password
        dict_reader_name: Optional dict reader user name
        dict_reader_password: Optional dict reader password
        mcp_user_name: Optional MCP user name
        mcp_password: Optional MCP user password

    Returns:
        Complete SQL string for bootstrap
    """
    lines = [
        "-- Bootstrap script for ClickHouse database",
        "-- Safe to run multiple times (idempotent)",
        "",
        "-- Create database",
        f"CREATE DATABASE IF NOT EXISTS {db};",
        "",
        "-- =============================================================================",
        "-- ROLES",
        "-- =============================================================================",
        "",
        "-- Migration role: full access for schema changes",
        f"CREATE ROLE IF NOT EXISTS {project}_migration_role;",
        f"GRANT ALL ON {db}.* TO {project}_migration_role;",
        f"GRANT CREATE TEMPORARY TABLE ON *.* TO {project}_migration_role;",
    ]

    # MCP readonly role (optional)
    if mcp_user_name and mcp_password:
        lines.extend(
            [
                "",
                "-- Read-only role: for MCP tools",
                f"CREATE ROLE IF NOT EXISTS {project}_readonly_role;",
                f"GRANT SELECT ON {db}.* TO {project}_readonly_role;",
                f"GRANT SHOW TABLES ON {db}.* TO {project}_readonly_role;",
            ]
        )

    # Dict reader role (optional)
    if dict_reader_name and dict_reader_password:
        lines.extend(
            [
                "",
                "-- Dict reader role: for dictionary sources",
                f"CREATE ROLE IF NOT EXISTS {project}_dict_role;",
                "-- SELECT grants added per-table when dictionaries are created",
            ]
        )

    lines.extend(
        [
            "",
            "-- =============================================================================",
            "-- USERS",
            "-- =============================================================================",
            "",
            "-- Migration user (required)",
            f"CREATE USER IF NOT EXISTS {migration_user}",
            f"IDENTIFIED BY '{escape_sql_string(migration_password)}';",
            f"GRANT {project}_migration_role TO {migration_user};",
        ]
    )

    # MCP user (optional)
    if mcp_user_name and mcp_password:
        lines.extend(
            [
                "",
                "-- MCP user: read-only access for AI tools",
                f"CREATE USER IF NOT EXISTS {mcp_user_name}",
                f"IDENTIFIED BY '{escape_sql_string(mcp_password)}';",
                f"GRANT {project}_readonly_role TO {mcp_user_name};",
            ]
        )

    # Dict reader user (optional)
    if dict_reader_name and dict_reader_password:
        lines.extend(
            [
                "",
                "-- Dict reader user: for dictionary sources",
                f"CREATE USER IF NOT EXISTS {dict_reader_name}",
                f"IDENTIFIED BY '{escape_sql_string(dict_reader_password)}';",
                f"GRANT {project}_dict_role TO {dict_reader_name};",
            ]
        )

    return "\n".join(lines)


def run_bootstrap(
    env_name: str,
    config_path: Optional[Path] = None,
    dry_run: bool = False,
) -> None:
    """
    Run bootstrap for the specified environment.

    Args:
        env_name: Environment name (dev, staging, production, etc.)
        config_path: Path to config.yaml (defaults to ./config.yaml)
        dry_run: If True, print SQL without executing
    """
    if config_path is None:
        config_path = Path.cwd() / "config.yaml"

    print(f"==> Loading environment: {env_name}")
    env_config = get_env_config(env_name, config_path)

    # Get SSM paths if configured
    ssm_config = env_config.get("ssm", {})

    # Get required credentials
    admin_password = get_secret(
        env_name,
        "admin_password",
        ssm_path=ssm_config.get("admin_password"),
        required=True,
    )

    migration_password = get_secret(
        env_name,
        "migration_password",
        ssm_path=ssm_config.get("migration_password"),
        required=True,
    )
    assert admin_password is not None  # required=True ensures this
    assert migration_password is not None  # required=True ensures this

    # Get optional credentials
    dict_reader_name = env_config.get("dict_reader_name")
    dict_reader_password = None
    if dict_reader_name:
        dict_reader_password = get_secret(
            env_name,
            "dict_reader_password",
            ssm_path=ssm_config.get("dict_reader_password"),
            required=True,
        )

    mcp_user_name = env_config.get("mcp_user_name")
    mcp_password = None
    if mcp_user_name:
        mcp_password = get_secret(
            env_name,
            "mcp_password",
            ssm_path=ssm_config.get("mcp_password"),
            required=True,
        )

    # Get migration user - support both new 'migration_user' and legacy 'user' field
    migration_user = env_config.get("migration_user") or env_config.get("user")
    if not migration_user:
        raise ValueError(f"migration_user is required in config.yaml for environment '{env_name}'")

    # Build SQL
    project_config = env_config.get("project")
    if project_config:
        project = project_config
    else:
        # Derive from database name (e.g., myproject_dev -> myproject)
        project = env_config["database"].split("_")[0]

    sql = build_bootstrap_sql(
        project=project,
        db=env_config["database"],
        migration_user=migration_user,
        migration_password=migration_password,
        dict_reader_name=dict_reader_name,
        dict_reader_password=dict_reader_password,
        mcp_user_name=mcp_user_name,
        mcp_password=mcp_password,
    )

    if dry_run:
        print("==> Dry run - SQL that would be executed:")
        print("-" * 60)
        # Mask passwords in output
        masked_sql = sql
        for pw in [migration_password, dict_reader_password, mcp_password]:
            if pw:
                masked_sql = masked_sql.replace(pw, "********")
        print(masked_sql)
        print("-" * 60)
        return

    host = env_config["host"]
    admin_user = env_config.get("admin_user", "default")
    secure = env_config.get("secure", True)
    port = env_config.get("port", 8443 if secure else 8123)

    print(f"==> Connecting as admin: {admin_user}@{host}")
    print(f"==> Target database: {env_config['database']}")
    print(f"==> Migration user: {migration_user}")
    if dict_reader_name:
        print(f"==> Dict reader: {dict_reader_name}")
    if mcp_user_name:
        print(f"==> MCP user: {mcp_user_name}")

    client = clickhouse_connect.get_client(
        host=host,
        port=port,
        username=admin_user,
        password=admin_password,
        secure=secure,
        interface="https" if secure else "http",
    )

    # Execute each statement
    for statement in sql.split(";"):
        statement = statement.strip()
        if statement and not statement.startswith("--"):
            client.command(statement)

    print("==> Bootstrap complete!")
    print(f"\nYou can now run migrations:")
    print(f"  ch-migrate up {env_name}")


def main() -> None:
    """CLI entrypoint for bootstrap."""
    if len(sys.argv) < 2:
        print("Usage: ch-migrate bootstrap <environment> [--dry-run]")
        print("Example: ch-migrate bootstrap dev")
        sys.exit(1)

    dry_run = "--dry-run" in sys.argv
    env_name = sys.argv[1]

    try:
        run_bootstrap(env_name, dry_run=dry_run)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

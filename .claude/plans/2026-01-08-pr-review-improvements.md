# PR #2 Review Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Address 14 actionable PR review comments covering user/permission model, SSM credentials, bootstrap safety, CLI unification, and test coverage.

**Architecture:** Refactor bootstrap to use roles instead of direct grants, add optional dict_reader/MCP users, support SSM as credential source with .env precedence, unify CLI commands, ensure idempotent bootstrap operations.

**Tech Stack:** Python 3.9+, Click CLI, boto3 (optional for SSM), clickhouse-connect, pytest

---

## Task 1: Update pyproject.toml - Python Versions & Dependencies

**Files:**
- Modify: `pyproject.toml:8-20,21-28`

**Step 1: Write the version check test**

```python
# tests/test_package.py
"""Tests for package metadata."""

import clickhouse_alembic


def test_version_is_defined():
    assert hasattr(clickhouse_alembic, "__version__")
    assert clickhouse_alembic.__version__ == "0.1.0"
```

**Step 2: Run test to verify it passes (existing functionality)**

Run: `pytest tests/test_package.py -v`
Expected: PASS

**Step 3: Update pyproject.toml with Python 3.13/3.14 and boto3 optional dep**

```toml
[project]
name = "clickhouse-alembic"
version = "0.1.0"
description = "Alembic-based migrations for ClickHouse, optimized for ClickHouse Cloud"
authors = [{ name = "Dan Young" }]
license = { text = "MIT" }
readme = "README.md"
requires-python = ">=3.9"
keywords = ["clickhouse", "alembic", "migrations", "database", "schema"]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Programming Language :: Python :: 3.14",
    "Topic :: Database",
]
dependencies = [
    "alembic>=1.13.0",
    "click>=8.1.0",
    "clickhouse-connect>=0.7.0",
    "python-dotenv>=1.0.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
ssm = ["boto3>=1.28.0"]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "mypy>=1.5.0",
    "types-PyYAML",
]
```

Note: Removed `clickhouse-sqlalchemy` from core dependencies - it's not actually used.

**Step 4: Update tool.black target-version**

```toml
[tool.black]
line-length = 100
target-version = ["py39", "py310", "py311", "py312", "py313", "py314"]
```

**Step 5: Run tests to verify nothing broke**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 6: Commit**

```bash
git add pyproject.toml tests/test_package.py
git commit -m "[deps] Add Python 3.13/3.14 support, boto3 optional dep for SSM"
```

---

## Task 2: Add Tests for _parse_source_table Helper

**Files:**
- Modify: `tests/test_helpers.py`

**Step 1: Write the failing tests**

Add to `tests/test_helpers.py`:

```python
from clickhouse_alembic.helpers import _parse_source_table


class TestParseSourceTable:
    def test_parses_table_pattern(self):
        sql = """
        CREATE DICTIONARY mydb.dict_users
        (id UInt64, name String)
        PRIMARY KEY id
        SOURCE(CLICKHOUSE(TABLE 'users' DB 'mydb'))
        """
        assert _parse_source_table(sql) == "users"

    def test_parses_query_pattern(self):
        sql = """
        CREATE DICTIONARY mydb.dict_orders
        (id UInt64, total Decimal(10,2))
        PRIMARY KEY id
        SOURCE(CLICKHOUSE(QUERY 'SELECT id, total FROM mydb.orders WHERE active = 1'))
        """
        assert _parse_source_table(sql) == "orders"

    def test_returns_none_when_no_source(self):
        sql = "CREATE DICTIONARY mydb.dict_static (id UInt64) PRIMARY KEY id"
        assert _parse_source_table(sql) is None

    def test_handles_multiline_query(self):
        sql = """
        SOURCE(CLICKHOUSE(QUERY '
            SELECT id, name
            FROM mydb.customers
            WHERE status = 1
        '))
        """
        assert _parse_source_table(sql) == "customers"
```

**Step 2: Run tests to verify they pass (function already exists)**

Run: `pytest tests/test_helpers.py::TestParseSourceTable -v`
Expected: All PASS (function exists at `helpers.py:107`)

**Step 3: Commit**

```bash
git add tests/test_helpers.py
git commit -m "[tests] Add tests for _parse_source_table helper"
```

---

## Task 3: Create Secrets Module for SSM Support

**Files:**
- Create: `clickhouse_alembic/secrets.py`
- Create: `tests/test_secrets.py`

**Step 1: Write the failing tests**

```python
# tests/test_secrets.py
"""Tests for secrets module."""

import os
import pytest
from unittest.mock import Mock, patch

from clickhouse_alembic.secrets import get_secret, SSMSecretNotFoundError


class TestGetSecret:
    def test_returns_env_var_when_set(self, monkeypatch):
        monkeypatch.setenv("CH_DEV_PASSWORD", "from-env")
        result = get_secret("dev", "password")
        assert result == "from-env"

    def test_env_var_takes_precedence_over_ssm(self, monkeypatch):
        monkeypatch.setenv("CH_DEV_PASSWORD", "from-env")
        # Even with SSM config, env var wins
        result = get_secret(
            "dev",
            "password",
            ssm_path="/myproject/dev/password"
        )
        assert result == "from-env"

    def test_returns_none_when_not_required_and_missing(self, monkeypatch):
        monkeypatch.delenv("CH_DEV_DICT_READER_PASSWORD", raising=False)
        result = get_secret("dev", "dict_reader_password", required=False)
        assert result is None

    def test_raises_when_required_and_missing(self, monkeypatch):
        monkeypatch.delenv("CH_DEV_PASSWORD", raising=False)
        with pytest.raises(ValueError, match="CH_DEV_PASSWORD.*required"):
            get_secret("dev", "password", required=True)

    @patch("clickhouse_alembic.secrets._get_ssm_client")
    def test_falls_back_to_ssm_when_env_not_set(self, mock_get_client, monkeypatch):
        monkeypatch.delenv("CH_DEV_PASSWORD", raising=False)

        mock_client = Mock()
        mock_client.get_parameter.return_value = {
            "Parameter": {"Value": "from-ssm"}
        }
        mock_get_client.return_value = mock_client

        result = get_secret("dev", "password", ssm_path="/myproject/dev/password")
        assert result == "from-ssm"
        mock_client.get_parameter.assert_called_once_with(
            Name="/myproject/dev/password",
            WithDecryption=True
        )

    @patch("clickhouse_alembic.secrets._get_ssm_client")
    def test_raises_when_ssm_parameter_not_found(self, mock_get_client, monkeypatch):
        monkeypatch.delenv("CH_DEV_PASSWORD", raising=False)

        mock_client = Mock()
        mock_client.get_parameter.side_effect = Exception("ParameterNotFound")
        mock_get_client.return_value = mock_client

        with pytest.raises(SSMSecretNotFoundError):
            get_secret("dev", "password", ssm_path="/invalid/path", required=True)

    def test_raises_import_error_when_boto3_not_installed(self, monkeypatch):
        monkeypatch.delenv("CH_DEV_PASSWORD", raising=False)

        with patch.dict("sys.modules", {"boto3": None}):
            with pytest.raises(ImportError, match="boto3.*pip install clickhouse-alembic\\[ssm\\]"):
                get_secret("dev", "password", ssm_path="/some/path")
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_secrets.py -v`
Expected: FAIL with "No module named 'clickhouse_alembic.secrets'"

**Step 3: Write the implementation**

```python
# clickhouse_alembic/secrets.py
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
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_secrets.py -v`
Expected: All PASS

**Step 5: Export from package**

Add to `clickhouse_alembic/__init__.py`:

```python
from clickhouse_alembic.secrets import get_secret, SSMSecretNotFoundError
```

**Step 6: Commit**

```bash
git add clickhouse_alembic/secrets.py tests/test_secrets.py clickhouse_alembic/__init__.py
git commit -m "[secrets] Add SSM support with env var precedence"
```

---

## Task 4: Update Config Template - Rename user to migration_user, Add SSM

**Files:**
- Modify: `clickhouse_alembic/templates/project/config.yaml.template`
- Modify: `clickhouse_alembic/templates/project/env.local.example.template`

**Step 1: Update config.yaml.template**

```yaml
# ClickHouse Migration Configuration
# Generated by ch-migrate init

project:
  name: {project_name}

# Default settings inherited by all environments
defaults:
  port: 8443
  secure: true
  admin_user: default
  # Optional: dict_reader for dictionary sources
  # dict_reader_name: dict_reader
  # Optional: mcp_user for read-only MCP tool access
  # mcp_user_name: mcp_reader

# Environment-specific configuration
# Passwords loaded from: .env.local (CH_<ENV>_PASSWORD) or SSM (if configured)
environments:
  dev:
    host: your-dev-instance.clickhouse.cloud
    database: {project_name}_dev
    migration_user: migration_dev
    # Optional SSM paths (env vars take precedence)
    # ssm:
    #   admin_password: /{project_name}/dev/admin_password
    #   migration_password: /{project_name}/dev/migration_password
    #   dict_reader_password: /{project_name}/dev/dict_reader_password
    #   mcp_password: /{project_name}/dev/mcp_password

  staging:
    host: your-staging-instance.clickhouse.cloud
    database: {project_name}_staging
    migration_user: migration_staging

  production:
    host: your-prod-instance.clickhouse.cloud
    database: {project_name}
    migration_user: migration_prod
```

**Step 2: Update env.local.example.template**

```bash
# ClickHouse credentials - DO NOT COMMIT THIS FILE
# Copy to .env.local and fill in your passwords
#
# Alternative: Use SSM paths in config.yaml (env vars take precedence)
# See: https://github.com/DRYCodeWorks/clickhouse-migrate#ssm-setup

# Dev environment
CH_DEV_MIGRATION_PASSWORD=your-dev-migration-password
CH_DEV_ADMIN_PASSWORD=your-dev-admin-password
# Optional: only needed if dict_reader_name is configured
# CH_DEV_DICT_READER_PASSWORD=your-dev-dict-reader-password
# Optional: only needed if mcp_user_name is configured
# CH_DEV_MCP_PASSWORD=your-dev-mcp-password

# Staging environment
CH_STAGING_MIGRATION_PASSWORD=your-staging-migration-password
CH_STAGING_ADMIN_PASSWORD=your-staging-admin-password
# CH_STAGING_DICT_READER_PASSWORD=your-staging-dict-reader-password
# CH_STAGING_MCP_PASSWORD=your-staging-mcp-password

# Production environment
CH_PRODUCTION_MIGRATION_PASSWORD=your-prod-migration-password
CH_PRODUCTION_ADMIN_PASSWORD=your-prod-admin-password
# CH_PRODUCTION_DICT_READER_PASSWORD=your-prod-dict-reader-password
# CH_PRODUCTION_MCP_PASSWORD=your-prod-mcp-password
```

**Step 3: Commit**

```bash
git add clickhouse_alembic/templates/project/config.yaml.template \
        clickhouse_alembic/templates/project/env.local.example.template
git commit -m "[config] Rename user to migration_user, add SSM and MCP user support"
```

---

## Task 5: Rewrite init_users.sql with Roles

**Files:**
- Modify: `clickhouse_alembic/templates/bootstrap/init_users.sql`

**Step 1: Rewrite with role-based permissions**

```sql
-- Bootstrap script for ClickHouse database
-- Creates database, roles, and users
-- Safe to run multiple times (idempotent)

-- Create database (if not exists)
CREATE DATABASE IF NOT EXISTS {db};

-- =============================================================================
-- ROLES
-- =============================================================================

-- Migration role: full access for schema changes and data operations
CREATE ROLE IF NOT EXISTS {project}_migration_role;
GRANT ALL ON {db}.* TO {project}_migration_role;
GRANT CREATE TEMPORARY TABLE ON *.* TO {project}_migration_role;

-- Read-only role: for MCP tools and reporting (optional)
-- Only created if mcp_user is configured
{mcp_role_block}

-- Dict reader role: for dictionary sources (optional)
-- Only created if dict_reader is configured
{dict_role_block}

-- =============================================================================
-- USERS
-- =============================================================================

-- Migration user (required)
CREATE USER IF NOT EXISTS {migration_user}
IDENTIFIED BY '{migration_password}';
GRANT {project}_migration_role TO {migration_user};

-- MCP user (optional) - read-only access for AI tools
{mcp_user_block}

-- Dict reader user (optional) - for dictionary sources
{dict_user_block}
```

**Step 2: Commit**

```bash
git add clickhouse_alembic/templates/bootstrap/init_users.sql
git commit -m "[bootstrap] Rewrite init_users.sql with role-based permissions"
```

---

## Task 6: Update bootstrap.py - Idempotent with Optional Users

**Files:**
- Modify: `clickhouse_alembic/bootstrap.py`
- Create: `tests/test_bootstrap.py`

**Step 1: Write the tests**

```python
# tests/test_bootstrap.py
"""Tests for bootstrap module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from clickhouse_alembic.bootstrap import (
    build_bootstrap_sql,
    escape_sql_string,
)


class TestEscapeSqlString:
    def test_escapes_single_quotes(self):
        assert escape_sql_string("pass'word") == "pass''word"

    def test_escapes_backslashes(self):
        assert escape_sql_string("pass\\word") == "pass\\\\word"

    def test_handles_both(self):
        assert escape_sql_string("it's a\\test") == "it''s a\\\\test"


class TestBuildBootstrapSql:
    def test_includes_database_creation(self):
        sql = build_bootstrap_sql(
            project="myproject",
            db="myproject_dev",
            migration_user="migration_dev",
            migration_password="secret123",
        )
        assert "CREATE DATABASE IF NOT EXISTS myproject_dev" in sql

    def test_includes_migration_role_and_user(self):
        sql = build_bootstrap_sql(
            project="myproject",
            db="myproject_dev",
            migration_user="migration_dev",
            migration_password="secret123",
        )
        assert "CREATE ROLE IF NOT EXISTS myproject_migration_role" in sql
        assert "CREATE USER IF NOT EXISTS migration_dev" in sql
        assert "GRANT myproject_migration_role TO migration_dev" in sql

    def test_excludes_dict_reader_when_not_configured(self):
        sql = build_bootstrap_sql(
            project="myproject",
            db="myproject_dev",
            migration_user="migration_dev",
            migration_password="secret123",
        )
        assert "dict_reader" not in sql.lower()

    def test_includes_dict_reader_when_configured(self):
        sql = build_bootstrap_sql(
            project="myproject",
            db="myproject_dev",
            migration_user="migration_dev",
            migration_password="secret123",
            dict_reader_name="dict_reader",
            dict_reader_password="dictpass",
        )
        assert "CREATE USER IF NOT EXISTS dict_reader" in sql
        assert "myproject_dict_role" in sql

    def test_excludes_mcp_user_when_not_configured(self):
        sql = build_bootstrap_sql(
            project="myproject",
            db="myproject_dev",
            migration_user="migration_dev",
            migration_password="secret123",
        )
        assert "mcp" not in sql.lower()

    def test_includes_mcp_user_when_configured(self):
        sql = build_bootstrap_sql(
            project="myproject",
            db="myproject_dev",
            migration_user="migration_dev",
            migration_password="secret123",
            mcp_user_name="mcp_reader",
            mcp_password="mcppass",
        )
        assert "CREATE USER IF NOT EXISTS mcp_reader" in sql
        assert "myproject_readonly_role" in sql
        assert "GRANT SELECT ON myproject_dev.*" in sql
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_bootstrap.py -v`
Expected: FAIL (function signature changed)

**Step 3: Rewrite bootstrap.py**

```python
# clickhouse_alembic/bootstrap.py
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
        f"-- Migration role: full access for schema changes",
        f"CREATE ROLE IF NOT EXISTS {project}_migration_role;",
        f"GRANT ALL ON {db}.* TO {project}_migration_role;",
        f"GRANT CREATE TEMPORARY TABLE ON *.* TO {project}_migration_role;",
    ]

    # MCP readonly role (optional)
    if mcp_user_name and mcp_password:
        lines.extend([
            "",
            f"-- Read-only role: for MCP tools",
            f"CREATE ROLE IF NOT EXISTS {project}_readonly_role;",
            f"GRANT SELECT ON {db}.* TO {project}_readonly_role;",
            f"GRANT SHOW TABLES ON {db}.* TO {project}_readonly_role;",
        ])

    # Dict reader role (optional)
    if dict_reader_name and dict_reader_password:
        lines.extend([
            "",
            f"-- Dict reader role: for dictionary sources",
            f"CREATE ROLE IF NOT EXISTS {project}_dict_role;",
            "-- SELECT grants added per-table when dictionaries are created",
        ])

    lines.extend([
        "",
        "-- =============================================================================",
        "-- USERS",
        "-- =============================================================================",
        "",
        "-- Migration user (required)",
        f"CREATE USER IF NOT EXISTS {migration_user}",
        f"IDENTIFIED BY '{escape_sql_string(migration_password)}';",
        f"GRANT {project}_migration_role TO {migration_user};",
    ])

    # MCP user (optional)
    if mcp_user_name and mcp_password:
        lines.extend([
            "",
            f"-- MCP user: read-only access for AI tools",
            f"CREATE USER IF NOT EXISTS {mcp_user_name}",
            f"IDENTIFIED BY '{escape_sql_string(mcp_password)}';",
            f"GRANT {project}_readonly_role TO {mcp_user_name};",
        ])

    # Dict reader user (optional)
    if dict_reader_name and dict_reader_password:
        lines.extend([
            "",
            f"-- Dict reader user: for dictionary sources",
            f"CREATE USER IF NOT EXISTS {dict_reader_name}",
            f"IDENTIFIED BY '{escape_sql_string(dict_reader_password)}';",
            f"GRANT {project}_dict_role TO {dict_reader_name};",
        ])

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
        env_name, "admin_password",
        ssm_path=ssm_config.get("admin_password"),
        required=True,
    )

    migration_password = get_secret(
        env_name, "migration_password",
        ssm_path=ssm_config.get("migration_password"),
        required=True,
    )

    # Get optional credentials
    dict_reader_name = env_config.get("dict_reader_name")
    dict_reader_password = None
    if dict_reader_name:
        dict_reader_password = get_secret(
            env_name, "dict_reader_password",
            ssm_path=ssm_config.get("dict_reader_password"),
            required=True,
        )

    mcp_user_name = env_config.get("mcp_user_name")
    mcp_password = None
    if mcp_user_name:
        mcp_password = get_secret(
            env_name, "mcp_password",
            ssm_path=ssm_config.get("mcp_password"),
            required=True,
        )

    # Build SQL
    project = env_config.get("project", env_config["database"].split("_")[0])
    sql = build_bootstrap_sql(
        project=project,
        db=env_config["database"],
        migration_user=env_config["migration_user"],
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
    print(f"==> Migration user: {env_config['migration_user']}")
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
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_bootstrap.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add clickhouse_alembic/bootstrap.py tests/test_bootstrap.py
git commit -m "[bootstrap] Rewrite with roles, optional users, dry-run support"
```

---

## Task 7: Update config.py for New Field Names

**Files:**
- Modify: `clickhouse_alembic/config.py`

**Step 1: Read current config.py to understand structure**

Run: `cat clickhouse_alembic/config.py`

**Step 2: Update to support migration_user and backward compat**

Update `get_env_config` to:
- Support both `user` (legacy) and `migration_user` (new)
- Load SSM config section
- Support `mcp_user_name` field

**Step 3: Run existing tests**

Run: `pytest tests/ -v`
Expected: All PASS

**Step 4: Commit**

```bash
git add clickhouse_alembic/config.py
git commit -m "[config] Support migration_user field and SSM config"
```

---

## Task 8: Update CLI with All Migration Commands

**Files:**
- Modify: `clickhouse_alembic/cli.py`

**Step 1: Add migration commands wrapping alembic**

Add these commands to `cli.py`:

```python
@main.command()
@click.argument("environment")
@click.option("--dry-run", is_flag=True, help="Show SQL without executing")
def bootstrap(environment: str, dry_run: bool) -> None:
    """Initialize database and users for an environment."""
    from clickhouse_alembic.bootstrap import run_bootstrap
    try:
        run_bootstrap(environment, dry_run=dry_run)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("environment")
def up(environment: str) -> None:
    """Apply pending migrations."""
    _run_alembic(environment, ["upgrade", "head"])


@main.command()
@click.argument("environment")
@click.option("--revision", "-r", default="-1", help="Revision to downgrade to")
def down(environment: str, revision: str) -> None:
    """Rollback migrations."""
    _run_alembic(environment, ["downgrade", revision])


@main.command()
@click.argument("environment")
def status(environment: str) -> None:
    """Show migration status."""
    _run_alembic(environment, ["current", "-v"])


@main.command()
@click.argument("environment")
def history(environment: str) -> None:
    """Show migration history."""
    _run_alembic(environment, ["history", "-v"])


@main.command()
@click.argument("environment")
@click.argument("name")
def new(environment: str, name: str) -> None:
    """Create a new migration."""
    _run_alembic(environment, ["revision", "-m", name])


def _run_alembic(environment: str, args: list[str]) -> None:
    """Run alembic with environment configuration."""
    import subprocess
    from clickhouse_alembic.config import get_env_config

    config = get_env_config(environment)
    env = os.environ.copy()
    env["CH_DATABASE"] = config["database"]
    env["CH_HOST"] = config["host"]
    # ... set other env vars

    result = subprocess.run(
        ["alembic"] + args,
        env=env,
        cwd=Path.cwd(),
    )
    sys.exit(result.returncode)
```

**Step 2: Run CLI help to verify**

Run: `python -m clickhouse_alembic.cli --help`
Expected: Shows all commands (init, bootstrap, up, down, status, history, new)

**Step 3: Commit**

```bash
git add clickhouse_alembic/cli.py
git commit -m "[cli] Add all migration commands (up, down, status, history, new)"
```

---

## Task 9: Update README.md

**Files:**
- Modify: `README.md`
- Modify: `examples/basic/README.md`

**Step 1: Update main README.md**

Key changes:
- Change `pip install` to `uv add` / `uv pip install`
- Explain what `ch-migrate` does upfront
- Update config examples with `migration_user`
- Add SSM setup section
- Update CLI reference with all commands
- Remove references to `migrate.sh` as primary interface

**Step 2: Update examples/basic/README.md**

```markdown
# Basic Example

A minimal example showing clickhouse-alembic in action.

## What is ch-migrate?

`ch-migrate` is a CLI tool for managing ClickHouse schema migrations. It:
- Initializes project structure with config files
- Bootstraps databases with proper users and roles
- Runs Alembic migrations against ClickHouse

## Setup

1. Install the package:
   ```bash
   uv add clickhouse-alembic
   # or: pip install clickhouse-alembic
   ```

2. Initialize (already done in this example):
   ```bash
   ch-migrate init
   ```

3. Configure `config.yaml` with your ClickHouse host

4. Set up credentials (choose one):

   **Option A: Environment file**
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with real passwords
   ```

   **Option B: AWS SSM** (for production)
   ```yaml
   # In config.yaml, add ssm paths:
   environments:
     production:
       ssm:
         admin_password: /myproject/prod/admin_password
         migration_password: /myproject/prod/migration_password
   ```

5. Bootstrap:
   ```bash
   ch-migrate bootstrap dev
   ```

6. Run migrations:
   ```bash
   ch-migrate up dev
   ```
```

**Step 3: Commit**

```bash
git add README.md examples/basic/README.md
git commit -m "[docs] Update README with uv, ch-migrate CLI, SSM setup"
```

---

## Task 10: Clean Up Unused SQLAlchemy References

**Files:**
- Modify: `clickhouse_alembic/env.py`

**Step 1: Review env.py for SQLAlchemy usage**

The PR comments asked about SQLAlchemy references in env.py. Review and remove if not needed, or document why they're required for Alembic.

**Step 2: Add comment explaining Alembic requirement**

If SQLAlchemy is needed for Alembic internals, add a comment explaining this.

**Step 3: Commit**

```bash
git add clickhouse_alembic/env.py
git commit -m "[env] Document SQLAlchemy requirement for Alembic"
```

---

## Task 11: Final Integration Test

**Step 1: Run full test suite**

Run: `pytest tests/ -v --cov=clickhouse_alembic`
Expected: All tests PASS

**Step 2: Run isort and black**

Run: `isort clickhouse_alembic tests && black clickhouse_alembic tests`

**Step 3: Run mypy**

Run: `mypy clickhouse_alembic`
Expected: No errors

**Step 4: Final commit**

```bash
git add -A
git commit -m "[cleanup] Format code, fix any type errors"
```

---

## Summary

| Task | Description | Files |
|------|-------------|-------|
| 1 | Python 3.13/3.14, boto3 optional dep | pyproject.toml |
| 2 | Tests for _parse_source_table | tests/test_helpers.py |
| 3 | Secrets module with SSM support | secrets.py, tests/test_secrets.py |
| 4 | Config templates with migration_user, SSM | templates/*.template |
| 5 | Rewrite init_users.sql with roles | templates/bootstrap/init_users.sql |
| 6 | Bootstrap with optional users, dry-run | bootstrap.py, tests/test_bootstrap.py |
| 7 | Config.py for new field names | config.py |
| 8 | CLI with all migration commands | cli.py |
| 9 | README updates | README.md, examples/basic/README.md |
| 10 | Clean up SQLAlchemy references | env.py |
| 11 | Integration test and formatting | All files |

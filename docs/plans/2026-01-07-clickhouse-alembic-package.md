# ClickHouse-Alembic Package Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Extract and genericize the Metopio ClickHouse migration tooling into a standalone, MIT-licensed pip-installable package called `clickhouse-alembic`.

**Architecture:** A Python package that wraps Alembic with ClickHouse Cloud-specific patterns. Users install the package, run `ch-migrate init` to scaffold their project, then use `migrate.sh` for daily operations. Configuration is split: YAML for non-secrets (version controlled), environment variables for passwords (gitignored `.env.local`).

**Tech Stack:** Python 3.9+, Alembic, clickhouse-connect, clickhouse-sqlalchemy, PyYAML, python-dotenv

---

## Pre-Implementation

### Task 0: Archive Existing Implementation

**Files:**
- Move: `alembic/` → `examples/frost-legacy/`

**Step 1: Create examples directory and move existing alembic code**

```bash
cd /Users/danyoung/Freelance/clickhouse-tools
mkdir -p examples
git mv alembic examples/frost-legacy
```

**Step 2: Commit the archive**

```bash
git add -A
git commit -m "[clickhouse-alembic] Archive frost-legacy alembic implementation"
```

---

## Phase 1: Package Structure

### Task 1: Create Package Skeleton

**Files:**
- Create: `clickhouse_alembic/__init__.py`
- Create: `clickhouse_alembic/py.typed`
- Modify: `pyproject.toml`

**Step 1: Create package directory**

```bash
mkdir -p /Users/danyoung/Freelance/clickhouse-tools/clickhouse_alembic
```

**Step 2: Create `__init__.py` with public API**

```python
"""
clickhouse-alembic: Alembic-based migrations for ClickHouse Cloud.

Usage:
    from clickhouse_alembic import read_sql, get_db, get_config, create_dictionary
"""

__version__ = "0.1.0"

from clickhouse_alembic.helpers import (
    create_dictionary,
    get_config,
    get_db,
    read_sql,
)

__all__ = [
    "__version__",
    "read_sql",
    "get_db",
    "get_config",
    "create_dictionary",
]
```

**Step 3: Create `py.typed` marker**

```bash
touch /Users/danyoung/Freelance/clickhouse-tools/clickhouse_alembic/py.typed
```

**Step 4: Update `pyproject.toml`**

Replace the existing `[project]` section with:

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
    "Topic :: Database",
]
dependencies = [
    "alembic>=1.13.0",
    "clickhouse-connect>=0.7.0",
    "clickhouse-sqlalchemy>=0.3.0",
    "python-dotenv>=1.0.0",
    "pyyaml>=6.0",
]

[project.scripts]
ch-migrate = "clickhouse_alembic.cli:main"

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "mypy>=1.5.0",
    "types-PyYAML",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["clickhouse_alembic"]

[tool.black]
line-length = 100
target-version = ["py39", "py310", "py311", "py312"]

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
check_untyped_defs = true
```

**Step 5: Commit package skeleton**

```bash
git add clickhouse_alembic/ pyproject.toml
git commit -m "[clickhouse-alembic] Create package skeleton with public API"
```

---

### Task 2: Create Configuration Module

**Files:**
- Create: `clickhouse_alembic/config.py`
- Test: `tests/test_config.py`

**Step 1: Write failing test for config loading**

Create `tests/test_config.py`:

```python
"""Tests for configuration loading."""

import os
import tempfile
from pathlib import Path

import pytest

from clickhouse_alembic.config import load_config, get_env_config


class TestLoadConfig:
    def test_loads_yaml_config(self, tmp_path: Path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
project:
  name: test-project

defaults:
  port: 8443
  secure: true

environments:
  dev:
    host: dev.clickhouse.cloud
    database: testdb
    user: service_dev
""")
        config = load_config(config_file)

        assert config["project"]["name"] == "test-project"
        assert config["defaults"]["port"] == 8443
        assert config["environments"]["dev"]["host"] == "dev.clickhouse.cloud"

    def test_raises_on_missing_file(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "nonexistent.yaml")


class TestGetEnvConfig:
    def test_merges_defaults_with_environment(self, tmp_path: Path, monkeypatch):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
defaults:
  port: 8443
  secure: true
  admin_user: default

environments:
  dev:
    host: dev.clickhouse.cloud
    database: testdb
    user: service_dev
  prod:
    host: prod.clickhouse.cloud
    database: proddb
    user: service_prod
    port: 9443
""")
        monkeypatch.setenv("CH_DEV_PASSWORD", "dev-pass")
        monkeypatch.setenv("CH_DEV_ADMIN_PASSWORD", "admin-pass")

        env_config = get_env_config("dev", config_file)

        assert env_config["host"] == "dev.clickhouse.cloud"
        assert env_config["port"] == 8443  # from defaults
        assert env_config["password"] == "dev-pass"
        assert env_config["admin_password"] == "admin-pass"

    def test_environment_overrides_defaults(self, tmp_path: Path, monkeypatch):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
defaults:
  port: 8443

environments:
  prod:
    host: prod.clickhouse.cloud
    database: proddb
    user: service_prod
    port: 9443
""")
        monkeypatch.setenv("CH_PROD_PASSWORD", "prod-pass")

        env_config = get_env_config("prod", config_file)

        assert env_config["port"] == 9443  # overridden

    def test_raises_on_missing_password(self, tmp_path: Path, monkeypatch):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
environments:
  dev:
    host: dev.clickhouse.cloud
    database: testdb
    user: service_dev
""")
        # Don't set CH_DEV_PASSWORD

        with pytest.raises(ValueError, match="CH_DEV_PASSWORD"):
            get_env_config("dev", config_file)

    def test_raises_on_unknown_environment(self, tmp_path: Path):
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
environments:
  dev:
    host: dev.clickhouse.cloud
""")

        with pytest.raises(ValueError, match="Unknown environment"):
            get_env_config("staging", config_file)
```

**Step 2: Run test to verify it fails**

```bash
cd /Users/danyoung/Freelance/clickhouse-tools
uv run pytest tests/test_config.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'clickhouse_alembic.config'`

**Step 3: Write minimal implementation**

Create `clickhouse_alembic/config.py`:

```python
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
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_config.py -v
```

Expected: All tests PASS

**Step 5: Commit**

```bash
git add clickhouse_alembic/config.py tests/test_config.py
git commit -m "[clickhouse-alembic] Add configuration loading with YAML + env var secrets"
```

---

### Task 3: Create Helpers Module

**Files:**
- Create: `clickhouse_alembic/helpers.py`
- Test: `tests/test_helpers.py`

**Step 1: Write failing tests for helpers**

Create `tests/test_helpers.py`:

```python
"""Tests for migration helpers."""

import os
from pathlib import Path

import pytest

from clickhouse_alembic.helpers import read_sql, get_db


class TestReadSql:
    def test_reads_sql_file(self, tmp_path: Path, monkeypatch):
        sql_dir = tmp_path / "migrations" / "sql"
        sql_dir.mkdir(parents=True)
        sql_file = sql_dir / "test.sql"
        sql_file.write_text("SELECT 1")

        monkeypatch.chdir(tmp_path)

        result = read_sql("test.sql")
        assert result == "SELECT 1"

    def test_substitutes_placeholders(self, tmp_path: Path, monkeypatch):
        sql_dir = tmp_path / "migrations" / "sql"
        sql_dir.mkdir(parents=True)
        sql_file = sql_dir / "test.sql"
        sql_file.write_text("CREATE TABLE {db}.users (id UInt64)")

        monkeypatch.chdir(tmp_path)

        result = read_sql("test.sql", db="mydb")
        assert result == "CREATE TABLE mydb.users (id UInt64)"

    def test_raises_on_missing_file(self, tmp_path: Path, monkeypatch):
        sql_dir = tmp_path / "migrations" / "sql"
        sql_dir.mkdir(parents=True)
        monkeypatch.chdir(tmp_path)

        with pytest.raises(FileNotFoundError, match="SQL file not found"):
            read_sql("nonexistent.sql")


class TestGetDb:
    def test_returns_database_from_env(self, monkeypatch):
        monkeypatch.setenv("CH_DATABASE", "testdb")
        assert get_db() == "testdb"

    def test_returns_default_when_not_set(self, monkeypatch):
        monkeypatch.delenv("CH_DATABASE", raising=False)
        assert get_db() == "default"
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_helpers.py -v
```

Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write minimal implementation**

Create `clickhouse_alembic/helpers.py`:

```python
"""Helper functions for ClickHouse migrations."""

import os
import re
from pathlib import Path
from typing import Any

from alembic import op


def _get_sql_dir() -> Path:
    """Get the SQL directory relative to current working directory."""
    return Path.cwd() / "migrations" / "sql"


def read_sql(path: str, **kwargs: Any) -> str:
    """
    Read a SQL file and substitute placeholders.

    Args:
        path: Relative path from migrations/sql/ (e.g., "history/tables/users/001_abc.sql")
        **kwargs: Values to substitute (e.g., db="mydb", password="secret")

    Returns:
        SQL string with placeholders replaced

    Raises:
        FileNotFoundError: If the SQL file doesn't exist

    Example:
        >>> read_sql("history/tables/users/001_abc.sql", db="mydb")
        'CREATE TABLE mydb.users ...'
    """
    sql_path = _get_sql_dir() / path
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")

    sql = sql_path.read_text()
    return sql.format(**kwargs)


def get_db() -> str:
    """
    Get database name from environment.

    Returns:
        Database name from CH_DATABASE env var, or "default" if not set
    """
    return os.environ.get("CH_DATABASE", "default")


def get_config_value(key: str) -> str | None:
    """
    Get a configuration value from environment.

    Args:
        key: Environment variable name

    Returns:
        Value or None if not set
    """
    return os.environ.get(key)


def create_dictionary(path: str, *, db: str | None = None, password: str | None = None) -> None:
    """
    Create a dictionary with automatic SELECT grant for dict_reader.

    This helper:
    1. Reads the dictionary SQL file
    2. Parses the source table from the SQL
    3. Grants SELECT on that table to dict_reader
    4. Creates the dictionary

    Args:
        path: Relative path to dictionary SQL file
        db: Database name (defaults to get_db())
        password: dict_reader password (defaults to DICT_READER_PASSWORD env var)

    Example:
        create_dictionary("history/dictionaries/dict_users/001_abc.sql")
    """
    if db is None:
        db = get_db()
    if password is None:
        password = os.environ.get("DICT_READER_PASSWORD")
        if not password:
            raise ValueError(
                "DICT_READER_PASSWORD environment variable is required for dictionaries."
            )

    # Read and format the dictionary SQL
    dict_sql = read_sql(path, db=db, password=password)

    # Parse the source table from the SQL
    source_table = _parse_source_table(dict_sql)

    if source_table:
        # Grant SELECT to dict_reader before creating dictionary
        op.execute(f"GRANT SELECT ON {db}.{source_table} TO dict_reader")

    # Create the dictionary
    op.execute(dict_sql)


def _parse_source_table(dict_sql: str) -> str | None:
    """
    Parse the source table name from dictionary SQL.

    Supports two patterns:
    1. TABLE 'table_name' (simple table source)
    2. QUERY '...FROM db.table_name...' (query source)

    Returns:
        Table name or None if not found
    """
    # Try TABLE 'table_name' pattern first
    table_match = re.search(r"TABLE\s+'(\w+)'", dict_sql, re.IGNORECASE)
    if table_match:
        return table_match.group(1)

    # Try QUERY pattern: FROM db.table_name
    query_match = re.search(r"FROM\s+\w+\.(\w+)", dict_sql, re.IGNORECASE)
    if query_match:
        return query_match.group(1)

    return None
```

**Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_helpers.py -v
```

Expected: All tests PASS

**Step 5: Update `__init__.py` imports**

The imports should already work since we defined them in Task 1. Verify:

```bash
uv run python -c "from clickhouse_alembic import read_sql, get_db, create_dictionary; print('OK')"
```

**Step 6: Commit**

```bash
git add clickhouse_alembic/helpers.py tests/test_helpers.py
git commit -m "[clickhouse-alembic] Add migration helpers (read_sql, get_db, create_dictionary)"
```

---

### Task 4: Create Alembic Environment Module

**Files:**
- Create: `clickhouse_alembic/env.py`

**Step 1: Create the Alembic environment module**

This module is used by Alembic at runtime, so we'll test it through integration tests later.

Create `clickhouse_alembic/env.py`:

```python
"""
ClickHouse Alembic Environment.

This module is copied to user projects and configures Alembic for ClickHouse.
It loads configuration from config.yaml and secrets from environment variables.
"""

import os
from logging.config import fileConfig
from pathlib import Path
from urllib.parse import quote_plus

from alembic import context
from alembic.ddl import impl
from dotenv import load_dotenv
from sqlalchemy import create_engine, pool, text

from clickhouse_alembic.config import get_env_config

# Alembic Config object
config = context.config

# Get environment name from alembic -n flag
env_name = getattr(config.cmd_opts, "name", None) or "dev"

# Load .env.local for secrets (if it exists)
env_local = Path.cwd() / ".env.local"
if env_local.exists():
    load_dotenv(env_local)

# Load configuration
config_path = Path.cwd() / "config.yaml"
try:
    env_config = get_env_config(env_name, config_path)
except FileNotFoundError:
    raise FileNotFoundError(
        f"config.yaml not found in {Path.cwd()}\n"
        f"Run 'ch-migrate init' to create project structure."
    )

# Setup logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


class ClickhouseImpl(impl.DefaultImpl):
    """Alembic implementation for ClickHouse dialect."""
    __dialect__ = "clickhouse"
    transactional_ddl = False


def get_sqlalchemy_url() -> str:
    """Build SQLAlchemy-compatible ClickHouse URL from config."""
    host = env_config["host"]
    user = env_config["user"]
    password = env_config["password"]
    database = env_config["database"]
    port = env_config.get("port", 8443)
    secure = env_config.get("secure", True)

    # URL-encode password to handle special characters
    encoded_password = quote_plus(password)

    # Build SQLAlchemy URL
    protocol_param = "?protocol=https" if secure else ""
    return f"clickhouse+http://{user}:{encoded_password}@{host}:{port}/{database}{protocol_param}"


# Export database name for use in migrations
DATABASE_NAME = env_config["database"]
os.environ["CH_DATABASE"] = DATABASE_NAME


def bootstrap_version_table(connection) -> None:
    """
    Create alembic_version table with ClickHouse-compatible engine.

    Must be called before Alembic tries to use its version table.
    """
    db = DATABASE_NAME

    # Ensure database exists
    connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {db}"))
    connection.commit()

    # Check if version table exists
    result = connection.execute(text(f"""
        SELECT count() FROM system.tables
        WHERE database = '{db}' AND name = 'alembic_version'
    """))
    exists = result.scalar() > 0

    if not exists:
        # Create with ClickHouse Cloud compatible engine
        connection.execute(text(f"""
            CREATE TABLE {db}.alembic_version
            (
                `updated` DateTime DEFAULT now(),
                `version_num` String
            )
            ENGINE = SharedReplacingMergeTree('/clickhouse/tables/{{uuid}}/{{shard}}', '{{replica}}')
            ORDER BY updated
            SETTINGS index_granularity = 8192
        """))
        connection.commit()


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode - generates SQL without executing."""
    url = get_sqlalchemy_url()
    context.configure(
        url=url,
        target_metadata=None,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table="alembic_version",
        version_table_schema=DATABASE_NAME,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode - executes against the database."""
    connectable = create_engine(get_sqlalchemy_url(), poolclass=pool.NullPool)

    with connectable.connect() as connection:
        bootstrap_version_table(connection)

        context.configure(
            connection=connection,
            target_metadata=None,
            version_table="alembic_version",
            version_table_schema=DATABASE_NAME,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Step 2: Commit**

```bash
git add clickhouse_alembic/env.py
git commit -m "[clickhouse-alembic] Add Alembic environment module for ClickHouse"
```

---

### Task 5: Create Bootstrap Module

**Files:**
- Create: `clickhouse_alembic/bootstrap.py`
- Create: `clickhouse_alembic/templates/bootstrap/init_users.sql`

**Step 1: Create bootstrap SQL template**

```bash
mkdir -p /Users/danyoung/Freelance/clickhouse-tools/clickhouse_alembic/templates/bootstrap
```

Create `clickhouse_alembic/templates/bootstrap/init_users.sql`:

```sql
-- Bootstrap script for ClickHouse database
-- Creates database, dict_reader user, and service user

-- Create database
CREATE DATABASE IF NOT EXISTS {db};

-- Create dict_reader user (for dictionary sources)
CREATE USER IF NOT EXISTS {dict_reader_name}
IDENTIFIED BY '{dict_reader_password}';

-- Create service user (for migrations and application)
CREATE USER IF NOT EXISTS {service_user}
IDENTIFIED BY '{service_password}';

-- Grant permissions to service user
GRANT ALL ON {db}.* TO {service_user};
GRANT CREATE TEMPORARY TABLE ON *.* TO {service_user}
```

**Step 2: Create bootstrap module**

Create `clickhouse_alembic/bootstrap.py`:

```python
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
from importlib import resources

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
    port = 8443 if secure else 8123

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
```

**Step 3: Commit**

```bash
git add clickhouse_alembic/bootstrap.py clickhouse_alembic/templates/
git commit -m "[clickhouse-alembic] Add bootstrap module for database/user initialization"
```

---

### Task 6: Create CLI Module

**Files:**
- Create: `clickhouse_alembic/cli.py`
- Create: `clickhouse_alembic/templates/project/` (scaffolding templates)

**Step 1: Create project templates directory**

```bash
mkdir -p /Users/danyoung/Freelance/clickhouse-tools/clickhouse_alembic/templates/project
```

**Step 2: Create `alembic.ini` template**

Create `clickhouse_alembic/templates/project/alembic.ini.template`:

```ini
# ClickHouse Alembic Configuration
# Generated by ch-migrate init

[alembic]
script_location = migrations
prepend_sys_path = .
version_path_separator = os
file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d_%%(slug)s

# Environment sections - credentials come from config.yaml + .env.local
[dev]
script_location = migrations

[staging]
script_location = migrations

[production]
script_location = migrations

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S

[post_write_hooks]
hooks = black
black.type = console_scripts
black.entrypoint = black
```

**Step 3: Create `config.yaml` template**

Create `clickhouse_alembic/templates/project/config.yaml.template`:

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
  dict_reader_name: dict_reader

# Environment-specific configuration
# Passwords are loaded from environment variables: CH_<ENV>_PASSWORD, CH_<ENV>_ADMIN_PASSWORD
environments:
  dev:
    host: your-dev-instance.clickhouse.cloud
    database: {project_name}_dev
    user: service_dev

  staging:
    host: your-staging-instance.clickhouse.cloud
    database: {project_name}_staging
    user: service_staging

  production:
    host: your-prod-instance.clickhouse.cloud
    database: {project_name}
    user: service_prod
```

**Step 4: Create `.env.local.example` template**

Create `clickhouse_alembic/templates/project/env.local.example.template`:

```bash
# ClickHouse credentials - DO NOT COMMIT THIS FILE
# Copy to .env.local and fill in your passwords

# Dev environment
CH_DEV_PASSWORD=your-dev-service-password
CH_DEV_ADMIN_PASSWORD=your-dev-admin-password
CH_DEV_DICT_READER_PASSWORD=your-dev-dict-reader-password

# Staging environment
CH_STAGING_PASSWORD=your-staging-service-password
CH_STAGING_ADMIN_PASSWORD=your-staging-admin-password
CH_STAGING_DICT_READER_PASSWORD=your-staging-dict-reader-password

# Production environment
CH_PRODUCTION_PASSWORD=your-prod-service-password
CH_PRODUCTION_ADMIN_PASSWORD=your-prod-admin-password
CH_PRODUCTION_DICT_READER_PASSWORD=your-prod-dict-reader-password
```

**Step 5: Create `migrate.sh` template**

Create `clickhouse_alembic/templates/project/migrate.sh.template`:

```bash
#!/bin/bash
# ClickHouse Migration Helper
# Generated by ch-migrate init
#
# Usage: ./migrate.sh <environment> <command> [args]
#
# Commands:
#   bootstrap           - Initialize database and users (run once per environment)
#   status              - Show migration status (current/pending)
#   up [revision]       - Upgrade to revision (default: head for all pending)
#   down [revision]     - Rollback to revision (default: -1 for last migration)
#   new <name>          - Create new migration file
#   history             - Show migration history

set -e

ENV=${{1:-dev}}
CMD=${{2:-status}}
shift 2 2>/dev/null || true

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"

# Load .env.local if it exists
if [ -f "$SCRIPT_DIR/.env.local" ]; then
    set -a
    source "$SCRIPT_DIR/.env.local"
    set +a
fi

echo "==> Environment: $ENV"

cd "$SCRIPT_DIR"

case "$CMD" in
    bootstrap)
        echo "==> Bootstrapping database for $ENV"
        uv run python -c "from clickhouse_alembic.bootstrap import run_bootstrap; run_bootstrap('$ENV')"
        ;;
    status)
        CURRENT=$(uv run alembic -n "$ENV" current 2>/dev/null | grep -v "^\[" | grep -v "^INFO" | awk '{{print $1}}')
        echo "==> Migration history (current marked with *):"
        echo ""
        uv run alembic -n "$ENV" history 2>/dev/null | while read -r line; do
            to_rev=$(echo "$line" | sed 's/.*-> //' | awk '{{print $1}}' | tr -d ',')
            if [ "$to_rev" = "$CURRENT" ]; then
                echo "  * $line  <-- current"
            else
                echo "    $line"
            fi
        done
        echo ""
        ;;
    up)
        TARGET="${{1:-head}}"
        if [ "$TARGET" = "head" ]; then
            echo "==> Upgrading to head..."
        else
            echo "==> Upgrading to revision: $TARGET"
        fi
        uv run alembic -n "$ENV" upgrade "$TARGET"
        ;;
    down)
        TARGET="${{1:--1}}"
        if [ "$TARGET" = "-1" ]; then
            echo "==> Rolling back one migration..."
        else
            echo "==> Rolling back to revision: $TARGET"
        fi
        uv run alembic -n "$ENV" downgrade "$TARGET"
        ;;
    new)
        if [ -z "$1" ]; then
            echo "Error: Migration name required"
            echo "Usage: ./migrate.sh $ENV new <migration_name>"
            exit 1
        fi
        echo "==> Creating new migration: $1"
        uv run alembic -n "$ENV" revision -m "$1"
        ;;
    history)
        echo "==> Migration history:"
        uv run alembic -n "$ENV" history
        ;;
    *)
        echo "Unknown command: $CMD"
        echo ""
        echo "Available commands: bootstrap, status, up, down, new, history"
        exit 1
        ;;
esac
```

**Step 6: Create `script.py.mako` template**

Create `clickhouse_alembic/templates/project/script.py.mako.template`:

```mako
"""${{message}}

Revision ID: ${{up_revision}}
Revises: ${{down_revision | comma,n}}
Create Date: ${{create_date}}
"""

from alembic import op

from clickhouse_alembic import get_db, read_sql

# revision identifiers
revision = ${{repr(up_revision)}}
down_revision = ${{repr(down_revision)}}
branch_labels = ${{repr(branch_labels)}}
depends_on = ${{repr(depends_on)}}


def upgrade() -> None:
    db = get_db()
    # TODO: Add your upgrade SQL here
    # op.execute(read_sql("history/tables/my_table/001_{}.sql".format(revision), db=db))
    pass


def downgrade() -> None:
    db = get_db()
    # TODO: Add your downgrade SQL here
    # op.execute(f"DROP TABLE IF EXISTS {db}.my_table")
    pass
```

**Step 7: Create CLI module**

Create `clickhouse_alembic/cli.py`:

```python
"""Command-line interface for clickhouse-alembic."""

import os
import shutil
import sys
from pathlib import Path

import click


def get_template_path(name: str) -> Path:
    """Get path to a template file."""
    return Path(__file__).parent / "templates" / "project" / f"{name}.template"


def render_template(template_path: Path, **kwargs) -> str:
    """Render a template with substitutions."""
    content = template_path.read_text()
    for key, value in kwargs.items():
        content = content.replace(f"{{{key}}}", value)
    return content


@click.group()
@click.version_option()
def main():
    """ClickHouse migration tool built on Alembic."""
    pass


@main.command()
@click.argument("path", default=".", type=click.Path())
@click.option("--name", "-n", default=None, help="Project name (defaults to directory name)")
def init(path: str, name: str | None):
    """Initialize a new ClickHouse migration project.

    Creates the project structure with config.yaml, migrate.sh, and migrations directory.
    """
    project_path = Path(path).resolve()

    if name is None:
        name = project_path.name

    # Normalize project name (replace spaces/hyphens with underscores for database names)
    safe_name = name.replace("-", "_").replace(" ", "_").lower()

    click.echo(f"Initializing ClickHouse migration project: {name}")
    click.echo(f"  Path: {project_path}")

    # Create directories
    project_path.mkdir(parents=True, exist_ok=True)
    (project_path / "migrations" / "sql" / "bootstrap").mkdir(parents=True, exist_ok=True)
    (project_path / "migrations" / "sql" / "history" / "tables").mkdir(parents=True, exist_ok=True)
    (project_path / "migrations" / "sql" / "history" / "views").mkdir(parents=True, exist_ok=True)
    (project_path / "migrations" / "sql" / "history" / "dictionaries").mkdir(parents=True, exist_ok=True)
    (project_path / "migrations" / "versions").mkdir(parents=True, exist_ok=True)

    # Copy/render templates
    templates = [
        ("alembic.ini", "alembic.ini"),
        ("config.yaml", "config.yaml"),
        ("env.local.example", ".env.local.example"),
        ("migrate.sh", "migrate.sh"),
        ("script.py.mako", "migrations/script.py.mako"),
    ]

    for template_name, output_name in templates:
        template_path = get_template_path(template_name)
        output_path = project_path / output_name

        if output_path.exists():
            click.echo(f"  Skipping {output_name} (already exists)")
            continue

        content = render_template(template_path, project_name=safe_name)
        output_path.write_text(content)
        click.echo(f"  Created {output_name}")

    # Make migrate.sh executable
    migrate_sh = project_path / "migrate.sh"
    if migrate_sh.exists():
        migrate_sh.chmod(0o755)

    # Copy env.py from package
    env_py_src = Path(__file__).parent / "env.py"
    env_py_dst = project_path / "migrations" / "env.py"
    if not env_py_dst.exists():
        shutil.copy(env_py_src, env_py_dst)
        click.echo("  Created migrations/env.py")

    # Create .gitignore
    gitignore_path = project_path / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text(".env.local\n__pycache__/\n*.pyc\n")
        click.echo("  Created .gitignore")

    click.echo("")
    click.echo("Project initialized! Next steps:")
    click.echo("")
    click.echo("  1. Edit config.yaml with your ClickHouse hosts")
    click.echo("  2. Copy .env.local.example to .env.local and add passwords")
    click.echo("  3. Run: ./migrate.sh dev bootstrap")
    click.echo("  4. Create your first migration: ./migrate.sh dev new create_users_table")


@main.command()
@click.argument("environment")
def bootstrap(environment: str):
    """Initialize database and users for an environment.

    Creates the database, dict_reader user, and service user.
    Requires admin credentials in .env.local.
    """
    from clickhouse_alembic.bootstrap import run_bootstrap

    try:
        run_bootstrap(environment)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Step 8: Commit**

```bash
git add clickhouse_alembic/cli.py clickhouse_alembic/templates/project/
git commit -m "[clickhouse-alembic] Add CLI with init and bootstrap commands"
```

---

## Phase 2: Documentation & Polish

### Task 7: Update README

**Files:**
- Modify: `README.md`

**Step 1: Replace README with package documentation**

Replace the contents of `README.md` with comprehensive documentation for the new package. (Content based on our design discussions - quick start, configuration, usage patterns, ClickHouse Cloud specifics.)

**Step 2: Commit**

```bash
git add README.md
git commit -m "[clickhouse-alembic] Update README with package documentation"
```

---

### Task 8: Add LICENSE File

**Files:**
- Create: `LICENSE`

**Step 1: Create MIT LICENSE file**

```
MIT License

Copyright (c) 2025 Dan Young

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

**Step 2: Commit**

```bash
git add LICENSE
git commit -m "[clickhouse-alembic] Add MIT license"
```

---

### Task 9: Create Basic Example

**Files:**
- Create: `examples/basic/README.md`
- Create: `examples/basic/config.yaml`
- Create: `examples/basic/migrations/sql/history/tables/users/001_example.sql`

**Step 1: Create example directory structure**

```bash
mkdir -p /Users/danyoung/Freelance/clickhouse-tools/examples/basic/migrations/sql/history/tables/users
```

**Step 2: Create example files**

Create `examples/basic/README.md`:

```markdown
# Basic Example

A minimal example showing clickhouse-alembic in action.

## Setup

1. Install the package:
   ```bash
   pip install clickhouse-alembic
   ```

2. Initialize (already done in this example):
   ```bash
   ch-migrate init
   ```

3. Configure `config.yaml` with your ClickHouse host

4. Create `.env.local` with your passwords

5. Bootstrap:
   ```bash
   ./migrate.sh dev bootstrap
   ```

6. Run migrations:
   ```bash
   ./migrate.sh dev up
   ```
```

Create `examples/basic/config.yaml`:

```yaml
project:
  name: basic-example

defaults:
  port: 8443
  secure: true
  admin_user: default
  dict_reader_name: dict_reader

environments:
  dev:
    host: localhost
    port: 8123
    secure: false
    database: basic_example
    user: default
```

Create `examples/basic/migrations/sql/history/tables/users/001_example.sql`:

```sql
-- Users table v1
CREATE TABLE {db}.users (
    id UInt64,
    email String,
    name String,
    created_at DateTime DEFAULT now()
)
ENGINE = SharedMergeTree
ORDER BY id
```

**Step 3: Commit**

```bash
git add examples/basic/
git commit -m "[clickhouse-alembic] Add basic usage example"
```

---

### Task 10: Final Cleanup & Test Install

**Step 1: Remove old files that are no longer needed at root**

Review and remove any files from the old clickhouse-tools structure that are now redundant (keep ch.py and other tools that aren't part of clickhouse-alembic).

**Step 2: Test package installation**

```bash
cd /Users/danyoung/Freelance/clickhouse-tools
uv pip install -e .
ch-migrate --version
ch-migrate --help
```

**Step 3: Test init command**

```bash
cd /tmp
mkdir test-project
cd test-project
ch-migrate init
ls -la
cat config.yaml
```

**Step 4: Clean up test project**

```bash
rm -rf /tmp/test-project
```

**Step 5: Final commit**

```bash
git add -A
git commit -m "[clickhouse-alembic] Final cleanup and verification"
```

---

## Summary

This plan creates a pip-installable `clickhouse-alembic` package with:

1. **Configuration**: YAML for non-secrets, env vars for passwords
2. **Helpers**: `read_sql()`, `get_db()`, `create_dictionary()`
3. **CLI**: `ch-migrate init` and `ch-migrate bootstrap`
4. **Templates**: Project scaffolding for new migrations projects
5. **Documentation**: README, examples, MIT license

The existing frost-legacy implementation is preserved in `examples/` for reference.

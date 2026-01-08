"""Tests for bootstrap module."""

import pytest

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

    def test_escapes_passwords_in_sql(self):
        sql = build_bootstrap_sql(
            project="myproject",
            db="myproject_dev",
            migration_user="migration_dev",
            migration_password="pass'word",
        )
        assert "pass''word" in sql
        assert "pass'word" not in sql

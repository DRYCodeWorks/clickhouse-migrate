"""Tests for migration helpers."""

from pathlib import Path

import pytest

from clickhouse_alembic.helpers import get_db, read_sql


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

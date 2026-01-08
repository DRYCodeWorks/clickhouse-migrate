"""Tests for package metadata."""

import clickhouse_alembic


def test_version_is_defined():
    assert hasattr(clickhouse_alembic, "__version__")
    assert clickhouse_alembic.__version__ == "0.1.0"

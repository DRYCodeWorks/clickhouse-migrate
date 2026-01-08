"""Tests for secrets module."""

import json
from unittest.mock import Mock, patch

import pytest

from clickhouse_alembic.secrets import (
    SSMJsonKeyError,
    SSMSecretNotFoundError,
    _parse_ssm_path,
    get_secret,
)


class TestGetSecret:
    def test_returns_env_var_when_set(self, monkeypatch):
        monkeypatch.setenv("CH_DEV_PASSWORD", "from-env")
        result = get_secret("dev", "password")
        assert result == "from-env"

    @patch("clickhouse_alembic.secrets._get_ssm_client")
    def test_ssm_takes_precedence_when_path_configured(self, mock_get_client, monkeypatch):
        # Even with env var set, SSM is used when ssm_path is provided
        monkeypatch.setenv("CH_DEV_PASSWORD", "from-env")

        mock_client = Mock()
        mock_client.get_parameter.return_value = {"Parameter": {"Value": "from-ssm"}}
        mock_get_client.return_value = mock_client

        result = get_secret("dev", "password", ssm_path="/myproject/dev/password")
        assert result == "from-ssm"
        mock_client.get_parameter.assert_called_once()

    def test_returns_none_when_not_required_and_missing(self, monkeypatch):
        monkeypatch.delenv("CH_DEV_DICT_READER_PASSWORD", raising=False)
        result = get_secret("dev", "dict_reader_password", required=False)
        assert result is None

    def test_raises_when_required_and_missing(self, monkeypatch):
        monkeypatch.delenv("CH_DEV_PASSWORD", raising=False)
        with pytest.raises(ValueError, match="CH_DEV_PASSWORD.*required"):
            get_secret("dev", "password", required=True)

    @patch("clickhouse_alembic.secrets._get_ssm_client")
    def test_fetches_from_ssm_when_path_configured(self, mock_get_client, monkeypatch):
        monkeypatch.delenv("CH_DEV_PASSWORD", raising=False)

        mock_client = Mock()
        mock_client.get_parameter.return_value = {"Parameter": {"Value": "from-ssm"}}
        mock_get_client.return_value = mock_client

        result = get_secret("dev", "password", ssm_path="/myproject/dev/password")
        assert result == "from-ssm"
        mock_client.get_parameter.assert_called_once_with(
            Name="/myproject/dev/password", WithDecryption=True
        )

    @patch("clickhouse_alembic.secrets._get_ssm_exceptions")
    @patch("clickhouse_alembic.secrets._get_ssm_client")
    def test_raises_when_ssm_parameter_not_found(
        self, mock_get_client, mock_get_exceptions, monkeypatch
    ):
        monkeypatch.delenv("CH_DEV_PASSWORD", raising=False)

        # Create a mock ClientError with proper response structure
        class MockClientError(Exception):
            def __init__(self, error_code):
                self.response = {"Error": {"Code": error_code}}
                super().__init__(error_code)

        mock_get_exceptions.return_value = MockClientError

        mock_client = Mock()
        mock_client.get_parameter.side_effect = MockClientError("ParameterNotFound")
        mock_get_client.return_value = mock_client

        with pytest.raises(SSMSecretNotFoundError):
            get_secret("dev", "password", ssm_path="/invalid/path", required=True)

    def test_raises_import_error_when_boto3_not_installed(self, monkeypatch):
        monkeypatch.delenv("CH_DEV_PASSWORD", raising=False)

        with patch.dict("sys.modules", {"boto3": None}):
            with pytest.raises(ImportError, match="boto3.*pip install clickhouse-alembic\\[ssm\\]"):
                get_secret("dev", "password", ssm_path="/some/path")


class TestParseSSMPath:
    def test_simple_string_path(self):
        path, json_key = _parse_ssm_path("/myproject/dev/password")
        assert path == "/myproject/dev/password"
        assert json_key is None

    def test_string_path_with_hash_suffix(self):
        path, json_key = _parse_ssm_path("/database/credentials#password")
        assert path == "/database/credentials"
        assert json_key == "password"

    def test_dict_path_without_json_key(self):
        path, json_key = _parse_ssm_path({"path": "/myproject/dev/password"})
        assert path == "/myproject/dev/password"
        assert json_key is None

    def test_dict_path_with_json_key(self):
        path, json_key = _parse_ssm_path({"path": "/database/credentials", "json_key": "password"})
        assert path == "/database/credentials"
        assert json_key == "password"


class TestSSMJsonKeyExtraction:
    @patch("clickhouse_alembic.secrets._get_ssm_client")
    def test_extracts_json_key_with_hash_suffix(self, mock_get_client):
        mock_client = Mock()
        mock_client.get_parameter.return_value = {
            "Parameter": {"Value": json.dumps({"password": "secret123", "user": "admin"})}
        }
        mock_get_client.return_value = mock_client

        result = get_secret("dev", "password", ssm_path="/database/credentials#password")
        assert result == "secret123"
        mock_client.get_parameter.assert_called_once_with(
            Name="/database/credentials", WithDecryption=True
        )

    @patch("clickhouse_alembic.secrets._get_ssm_client")
    def test_extracts_json_key_with_dict_syntax(self, mock_get_client):
        mock_client = Mock()
        mock_client.get_parameter.return_value = {
            "Parameter": {"Value": json.dumps({"password": "secret456", "user": "root"})}
        }
        mock_get_client.return_value = mock_client

        result = get_secret(
            "dev",
            "password",
            ssm_path={"path": "/database/credentials", "json_key": "password"},
        )
        assert result == "secret456"

    @patch("clickhouse_alembic.secrets._get_ssm_client")
    def test_raises_when_json_key_not_found(self, mock_get_client):
        mock_client = Mock()
        mock_client.get_parameter.return_value = {
            "Parameter": {"Value": json.dumps({"user": "admin"})}
        }
        mock_get_client.return_value = mock_client

        with pytest.raises(SSMJsonKeyError, match="JSON key 'password' not found"):
            get_secret("dev", "password", ssm_path="/database/credentials#password")

    @patch("clickhouse_alembic.secrets._get_ssm_client")
    def test_raises_when_value_not_valid_json(self, mock_get_client):
        mock_client = Mock()
        mock_client.get_parameter.return_value = {"Parameter": {"Value": "not-json"}}
        mock_get_client.return_value = mock_client

        with pytest.raises(SSMJsonKeyError, match="not valid JSON"):
            get_secret("dev", "password", ssm_path="/database/credentials#password")

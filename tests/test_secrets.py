"""Tests for secrets module."""

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

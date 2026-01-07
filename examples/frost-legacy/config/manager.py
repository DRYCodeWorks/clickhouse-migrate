"""
Configuration manager for ClickHouse migration tool.

This module handles loading and processing configuration files,
managing credentials from various sources, and generating
environment-specific settings.

Author: Dan Young
License: MIT License
Copyright (c) 2025 Dan Young
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union
from urllib.parse import quote

try:
    import boto3
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False


class ConfigurationError(Exception):
    """Raised when there's an error in configuration loading or processing"""
    pass


class CredentialProvider:
    """Base class for credential providers"""
    
    def get_credentials(self, environment: str) -> Dict[str, str]:
        """Get credentials for a specific environment"""
        raise NotImplementedError


class EnvVarsCredentialProvider(CredentialProvider):
    """Credential provider that uses environment variables"""
    
    def __init__(self, config: Dict[str, Any]):
        self.patterns = config
    
    def get_credentials(self, environment: str) -> Dict[str, str]:
        """Get credentials from environment variables"""
        env_upper = environment.upper()
        credentials = {}
        
        for key, pattern in self.patterns.items():
            env_var = pattern.format(env_upper=env_upper, environment=environment)
            value = os.environ.get(env_var)
            if value:
                credentials[key] = value
        
        return credentials


class AWSSecretsCredentialProvider(CredentialProvider):
    """Credential provider that uses AWS Secrets Manager"""
    
    def __init__(self, config: Dict[str, Any]):
        if not AWS_AVAILABLE:
            raise ConfigurationError("boto3 not available for AWS Secrets Manager")
        
        self.region = config.get("region", "us-east-1")
        self.secret_mappings = config.get("secret_mappings", {})
        self.client = boto3.client("secretsmanager", region_name=self.region)
    
    def get_credentials(self, environment: str) -> Dict[str, str]:
        """Get credentials from AWS Secrets Manager"""
        secret_id = self.secret_mappings.get(environment)
        if not secret_id:
            raise ConfigurationError(f"No secret mapping found for environment: {environment}")
        
        try:
            response = self.client.get_secret_value(SecretId=secret_id)
            return json.loads(response["SecretString"])
        except Exception as e:
            raise ConfigurationError(f"Failed to retrieve secret {secret_id}: {str(e)}")


class AWSSSMCredentialProvider(CredentialProvider):
    """Credential provider that uses AWS Systems Manager Parameter Store"""
    
    def __init__(self, config: Dict[str, Any]):
        if not AWS_AVAILABLE:
            raise ConfigurationError("boto3 not available for AWS SSM")
        
        self.region = config.get("region", "us-east-1")
        self.parameter_mappings = config.get("parameter_mappings", {})
        self.client = boto3.client("ssm", region_name=self.region)
    
    def get_credentials(self, environment: str) -> Dict[str, str]:
        """Get credentials from AWS SSM Parameter Store"""
        parameter_path = self.parameter_mappings.get(environment)
        if not parameter_path:
            raise ConfigurationError(f"No parameter mapping found for environment: {environment}")
        
        try:
            # Get all parameters under the path
            response = self.client.get_parameters_by_path(
                Path=parameter_path,
                Recursive=True,
                WithDecryption=True
            )
            
            credentials = {}
            for param in response["Parameters"]:
                # Extract the key from the parameter name (last part after /)
                key = param["Name"].split("/")[-1]
                credentials[key] = param["Value"]
            
            return credentials
        except Exception as e:
            raise ConfigurationError(f"Failed to retrieve parameters from {parameter_path}: {str(e)}")


class ConfigManager:
    """Main configuration manager class"""
    
    CREDENTIAL_PROVIDERS = {
        "env_vars": EnvVarsCredentialProvider,
        "aws_secrets": AWSSecretsCredentialProvider,
        "aws_ssm": AWSSSMCredentialProvider,
    }
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to configuration file. If None, looks for config.yaml in current dir
        """
        if config_path is None:
            config_path = Path.cwd() / "config" / "config.yaml"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.credential_provider = self._init_credential_provider()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse configuration file: {str(e)}")
    
    def _init_credential_provider(self) -> CredentialProvider:
        """Initialize the appropriate credential provider"""
        creds_config = self.config.get("credentials", {})
        provider_type = creds_config.get("type", "env_vars")
        
        if provider_type not in self.CREDENTIAL_PROVIDERS:
            raise ConfigurationError(f"Unknown credential provider type: {provider_type}")
        
        provider_class = self.CREDENTIAL_PROVIDERS[provider_type]
        provider_config = creds_config.get(provider_type, {})
        
        return provider_class(provider_config)
    
    def get_environment_config(self, environment: str) -> Dict[str, Any]:
        """Get complete configuration for a specific environment"""
        env_config = self.config.get("environments", {}).get(environment)
        if not env_config:
            raise ConfigurationError(f"Environment not found in configuration: {environment}")
        
        # Get credentials and merge them in
        try:
            credentials = self.credential_provider.get_credentials(environment)
        except Exception as e:
            # Log warning but don't fail - allow for environments without credentials
            credentials = {}
        
        # Build the complete configuration
        result = {
            **env_config,
            **credentials
        }
        
        return result
    
    def generate_sqlalchemy_url(self, environment: str) -> str:
        """Generate SQLAlchemy connection URL for an environment"""
        env_config = self.get_environment_config(environment)
        
        # Extract connection parameters
        host = env_config.get("host", "localhost")
        port = env_config.get("port", 8123)
        database = env_config.get("database", "default")
        username = env_config.get("username", "")
        password = env_config.get("password", "")
        protocol = env_config.get("protocol", "http")
        
        # URL encode password if it contains special characters
        if password and "%" in password:
            password = quote(password).replace("%", "%%")
        
        # Build ClickHouse connection URL
        if username and password:
            auth_part = f"{username}:{password}@"
        elif username:
            auth_part = f"{username}@"
        else:
            auth_part = ""
        
        protocol_param = f"?protocol={protocol}" if protocol == "https" else ""
        
        return f"clickhouse+http://{auth_part}{host}:{port}/{database}{protocol_param}"
    
    def get_environment_list(self) -> list:
        """Get list of configured environments"""
        return list(self.config.get("environments", {}).keys())
    
    def generate_alembic_ini(self, output_path: Optional[Union[str, Path]] = None) -> str:
        """Generate alembic.ini file from configuration"""
        if output_path is None:
            output_path = Path.cwd() / "alembic.ini"
        
        # Load the template
        template_path = Path(__file__).parent / "templates" / "alembic.ini.template"
        
        if not template_path.exists():
            raise ConfigurationError(f"Template file not found: {template_path}")
        
        with open(template_path, 'r') as f:
            template = f.read()
        
        # Get configuration values
        environments = ", ".join(self.get_environment_list())
        migration_config = self.config.get("migration", {})
        file_template = migration_config.get("file_template", 
                                            "%%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d_%%(slug)s")
        
        # Generate environment sections
        environment_sections = []
        version_locations = migration_config.get("version_locations", {})
        
        for env in self.get_environment_list():
            url = self.generate_sqlalchemy_url(env)
            # Determine version location - prefer clickhouse, fallback to default
            location = version_locations.get("clickhouse", "clickhouse_migrations")
            
            section = f"""[{env}]
sqlalchemy.url = {url}
version_locations = {location}"""
            environment_sections.append(section)
        
        # Generate hooks section
        hooks_config = migration_config.get("hooks", {})
        if hooks_config.get("enabled", True):
            formatters = hooks_config.get("formatters", ["black"])
            hooks_lines = ["hooks = " + ", ".join(formatters)]
            for formatter in formatters:
                hooks_lines.extend([
                    f"{formatter}.type = console_scripts",
                    f"{formatter}.entrypoint = {formatter}"
                ])
            hooks_section = "\n".join(hooks_lines)
        else:
            hooks_section = "# hooks disabled"
        
        # Fill in the template
        content = template.format(
            environments=environments,
            file_template=file_template,
            environment_sections="\n\n".join(environment_sections),
            hooks_section=hooks_section
        )
        
        # Write to file if output_path provided
        if output_path:
            with open(output_path, 'w') as f:
                f.write(content)
        
        return content
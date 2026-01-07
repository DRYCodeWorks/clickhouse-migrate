"""
ClickHouse connection manager for multiple projects and environments.
Handles connection pooling, credential management, and query execution.
"""

import os
import sys
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import yaml
import clickhouse_connect
from clickhouse_connect.driver import Client
import keyring
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

# Load environment variables
load_dotenv()

console = Console()


class ConnectionManager:
    """Manages ClickHouse connections for multiple projects and environments."""

    def __init__(self, config_path: str = "projects.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.connections: Dict[str, Client] = {}

    def _load_config(self) -> dict:
        """Load project configuration from YAML file."""
        if not self.config_path.exists():
            console.print(f"[red]Configuration file {self.config_path} not found![/red]")
            sys.exit(1)

        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def _get_credentials(self, project: str, env: str) -> Tuple[str, str]:
        """
        Get credentials for a project/environment.
        Tries in order: environment variables, keyring, prompt.
        """
        storage_method = self.config.get('settings', {}).get('credential_storage', 'env')

        # Construct environment variable names
        user_env = f"CH_{project.upper()}_{env.upper()}_USER"
        pass_env = f"CH_{project.upper()}_{env.upper()}_PASSWORD"

        # Try environment variables first
        username = os.getenv(user_env)
        password = os.getenv(pass_env)

        if username and password:
            return username, password

        # Try keyring if configured
        if storage_method == 'keyring':
            keyring_key = f"clickhouse-tools:{project}:{env}"
            stored_creds = keyring.get_password("clickhouse-tools", keyring_key)
            if stored_creds:
                username, password = stored_creds.split(':')
                return username, password

        # Fallback to prompt
        if not username:
            username = input(f"Enter username for {project}/{env}: ")
        if not password:
            import getpass
            password = getpass.getpass(f"Enter password for {project}/{env}: ")

        # Optionally save to keyring
        if storage_method == 'keyring':
            save = input("Save credentials to keyring? (y/n): ").lower()
            if save == 'y':
                keyring.set_password("clickhouse-tools", keyring_key, f"{username}:{password}")

        return username, password

    def get_connection_key(self, project: str, env: str) -> str:
        """Generate a unique key for connection pooling."""
        return f"{project}:{env}"

    def connect(self, project: str, env: str, force_new: bool = False) -> Client:
        """
        Get or create a connection to a ClickHouse instance.
        Uses connection pooling unless force_new is True.
        """
        key = self.get_connection_key(project, env)

        # Return existing connection if available and not forcing new
        if not force_new and key in self.connections:
            try:
                # Test if connection is still alive
                self.connections[key].ping()
                return self.connections[key]
            except:
                # Connection is dead, remove it
                del self.connections[key]

        # Validate project and environment
        if project not in self.config['projects']:
            raise ValueError(f"Unknown project: {project}")

        project_config = self.config['projects'][project]
        if env not in project_config['environments']:
            raise ValueError(f"Unknown environment for {project}: {env}")

        env_config = project_config['environments'][env]

        # Get credentials
        username, password = self._get_credentials(project, env)

        # Create connection
        try:
            client = clickhouse_connect.get_client(
                host=env_config['host'],
                port=env_config.get('port', 8443),
                username=username,
                password=password,
                database=env_config.get('database', 'default'),
                secure=env_config.get('secure', True),
                verify=env_config.get('verify', True),
                connect_timeout=self.config.get('settings', {}).get('connection_timeout', 10),
            )

            # Store in connection pool
            self.connections[key] = client

            console.print(f"[green]Connected to {project}/{env}[/green]")
            return client

        except Exception as e:
            console.print(f"[red]Failed to connect to {project}/{env}: {e}[/red]")
            raise

    def execute_query(
        self,
        project: str,
        env: str,
        query: str,
        params: Optional[Dict] = None,
        settings: Optional[Dict] = None
    ) -> Any:
        """Execute a query and return results."""
        client = self.connect(project, env)

        # Merge with default query settings
        query_settings = self.config.get('settings', {}).get('query_defaults', {}).copy()
        if settings:
            query_settings.update(settings)

        try:
            if params:
                # Parameterized query
                result = client.query(query, parameters=params, settings=query_settings)
            else:
                result = client.query(query, settings=query_settings)

            return result

        except Exception as e:
            console.print(f"[red]Query failed: {e}[/red]")
            raise

    def execute_file(
        self,
        project: str,
        env: str,
        file_path: str,
        params: Optional[Dict] = None,
        settings: Optional[Dict] = None
    ) -> Any:
        """Execute SQL from a file."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"SQL file not found: {file_path}")

        with open(path, 'r') as f:
            query = f.read()

        return self.execute_query(project, env, query, params, settings)

    def list_projects(self) -> List[str]:
        """List all configured projects."""
        return list(self.config['projects'].keys())

    def list_environments(self, project: str) -> List[str]:
        """List all environments for a project."""
        if project not in self.config['projects']:
            raise ValueError(f"Unknown project: {project}")
        return list(self.config['projects'][project]['environments'].keys())

    def get_database_name(self, project: str, env: str) -> str:
        """Get the database name for a project/environment."""
        env_config = self.config['projects'][project]['environments'][env]
        return env_config.get('database', 'default')

    def test_connection(self, project: str, env: str) -> bool:
        """Test if a connection can be established."""
        try:
            client = self.connect(project, env)
            result = client.query("SELECT 1")
            return True
        except Exception as e:
            console.print(f"[red]Connection test failed: {e}[/red]")
            return False

    def close_all(self):
        """Close all open connections."""
        for key, client in self.connections.items():
            try:
                client.close()
            except:
                pass
        self.connections.clear()

    def get_connection_info(self, project: str, env: str) -> Dict:
        """Get connection information (without credentials)."""
        if project not in self.config['projects']:
            raise ValueError(f"Unknown project: {project}")

        project_config = self.config['projects'][project]
        if env not in project_config['environments']:
            raise ValueError(f"Unknown environment for {project}: {env}")

        env_config = project_config['environments'][env]
        return {
            'host': env_config['host'],
            'port': env_config.get('port', 8443),
            'database': env_config.get('database', 'default'),
            'secure': env_config.get('secure', True),
        }

    def show_all_connections(self):
        """Display a table of all configured connections."""
        table = Table(title="Configured ClickHouse Connections")
        table.add_column("Project", style="cyan")
        table.add_column("Environment", style="magenta")
        table.add_column("Host", style="yellow")
        table.add_column("Database", style="green")
        table.add_column("Status", style="white")

        for project in self.list_projects():
            for env in self.list_environments(project):
                info = self.get_connection_info(project, env)
                key = self.get_connection_key(project, env)
                status = "🟢 Connected" if key in self.connections else "⚪ Not connected"

                table.add_row(
                    project,
                    env,
                    info['host'],
                    info['database'],
                    status
                )

        console.print(table)


# Convenience functions for command-line usage
def get_default_connection() -> Tuple[str, str]:
    """Get default project and environment from config."""
    config_path = Path("projects.yaml")
    if not config_path.exists():
        return None, None

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    settings = config.get('settings', {})
    return settings.get('default_project'), settings.get('default_environment')


def quick_query(query: str, project: Optional[str] = None, env: Optional[str] = None) -> Any:
    """Quick function to execute a query using defaults."""
    if not project or not env:
        default_project, default_env = get_default_connection()
        project = project or default_project
        env = env or default_env

    if not project or not env:
        raise ValueError("No project/environment specified and no defaults configured")

    manager = ConnectionManager()
    return manager.execute_query(project, env, query)
"""
User and role management for ClickHouse.
Provides standardized user creation, role assignment, and permission management.
"""

import secrets
import string
from typing import List, Dict, Optional, Any
from pathlib import Path
import yaml
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from connection import ConnectionManager

console = Console()


class UserManager:
    """Manages users and roles across ClickHouse projects and environments."""

    # Standard role templates
    ROLE_TEMPLATES = {
        'developer_admin': {
            'description': 'Full access to specific database for development',
            'grants': [
                "GRANT SELECT, INSERT, ALTER UPDATE, ALTER DELETE ON {database}.* TO {role_name}",
                "GRANT CREATE TABLE, DROP TABLE, TRUNCATE ON {database}.* TO {role_name}",
                "GRANT CREATE VIEW, DROP VIEW ON {database}.* TO {role_name}",
                "GRANT SHOW DATABASES, SHOW TABLES, SHOW COLUMNS ON {database}.* TO {role_name}",
            ]
        },
        'service': {
            'description': 'Service account with read/write access',
            'grants': [
                "GRANT SELECT, INSERT ON {database}.* TO {role_name}",
                "GRANT SHOW TABLES ON {database}.* TO {role_name}",
            ]
        },
        'readonly': {
            'description': 'Read-only access to database',
            'grants': [
                "GRANT SELECT ON {database}.* TO {role_name}",
                "GRANT SHOW TABLES, SHOW COLUMNS ON {database}.* TO {role_name}",
            ]
        },
        'analyst': {
            'description': 'Analyst role with read and create view permissions',
            'grants': [
                "GRANT SELECT ON {database}.* TO {role_name}",
                "GRANT CREATE VIEW, DROP VIEW ON {database}.* TO {role_name}",
                "GRANT SHOW TABLES, SHOW COLUMNS ON {database}.* TO {role_name}",
            ]
        },
        'admin': {
            'description': 'Full administrative access',
            'grants': [
                "GRANT ALL ON *.* TO {role_name} WITH GRANT OPTION",
            ]
        }
    }

    def __init__(self, connection_manager: Optional[ConnectionManager] = None):
        self.conn_manager = connection_manager or ConnectionManager()

    def generate_password(self, length: int = 32, special_chars: bool = True) -> str:
        """Generate a secure random password."""
        alphabet = string.ascii_letters + string.digits
        if special_chars:
            # Use a limited set of special chars to avoid shell escaping issues
            alphabet += "!@#$%^&*"

        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password

    def create_user(
        self,
        project: str,
        env: str,
        username: str,
        password: Optional[str] = None,
        auth_type: str = "sha256_password",
        host_restrictions: Optional[List[str]] = None
    ) -> str:
        """Create a new user in ClickHouse."""
        if not password:
            password = self.generate_password()
            console.print(f"[yellow]Generated password: {password}[/yellow]")
            console.print("[dim]Please save this password securely![/dim]")

        client = self.conn_manager.connect(project, env)

        # Build CREATE USER statement
        host_clause = ""
        if host_restrictions:
            hosts = ', '.join([f"'{host}'" for host in host_restrictions])
            host_clause = f" HOST {hosts}"

        create_query = f"""
        CREATE USER IF NOT EXISTS {username}
        IDENTIFIED WITH {auth_type} BY %(password)s
        {host_clause}
        """

        try:
            client.command(create_query, parameters={'password': password})
            console.print(f"[green]✓ User '{username}' created successfully[/green]")
            return password
        except Exception as e:
            console.print(f"[red]Failed to create user: {e}[/red]")
            raise

    def create_role(
        self,
        project: str,
        env: str,
        role_name: str,
        template: Optional[str] = None,
        custom_grants: Optional[List[str]] = None
    ):
        """Create a role with specified permissions."""
        client = self.conn_manager.connect(project, env)
        database = self.conn_manager.get_database_name(project, env)

        try:
            # Create the role
            client.command(f"CREATE ROLE IF NOT EXISTS {role_name}")
            console.print(f"[green]✓ Role '{role_name}' created[/green]")

            # Apply grants
            if template and template in self.ROLE_TEMPLATES:
                grants = self.ROLE_TEMPLATES[template]['grants']
                for grant in grants:
                    grant_sql = grant.format(database=database, role_name=role_name)
                    client.command(grant_sql)
                    console.print(f"[dim]  Applied: {grant_sql[:60]}...[/dim]")

            elif custom_grants:
                for grant in custom_grants:
                    client.command(grant)
                    console.print(f"[dim]  Applied: {grant[:60]}...[/dim]")

            console.print(f"[green]✓ Role '{role_name}' configured[/green]")

        except Exception as e:
            console.print(f"[red]Failed to create role: {e}[/red]")
            raise

    def grant_role(self, project: str, env: str, username: str, role_name: str, set_default: bool = True):
        """Grant a role to a user."""
        client = self.conn_manager.connect(project, env)

        try:
            # Grant the role
            client.command(f"GRANT {role_name} TO {username}")
            console.print(f"[green]✓ Granted role '{role_name}' to user '{username}'[/green]")

            # Set as default if requested
            if set_default:
                client.command(f"SET DEFAULT ROLE {role_name} TO {username}")
                console.print(f"[dim]  Set as default role[/dim]")

        except Exception as e:
            console.print(f"[red]Failed to grant role: {e}[/red]")
            raise

    def list_users(self, project: str, env: str) -> List[Dict]:
        """List all users in the database."""
        client = self.conn_manager.connect(project, env)

        query = """
        SELECT
            name,
            id,
            storage,
            auth_type,
            host_names,
            host_ips,
            default_roles_list
        FROM system.users
        ORDER BY name
        """

        result = client.query(query)
        users = []
        for row in result.result_rows:
            users.append({
                'name': row[0],
                'id': str(row[1]),
                'storage': row[2],
                'auth_type': row[3],
                'host_names': row[4],
                'host_ips': row[5],
                'default_roles': row[6]
            })

        return users

    def list_roles(self, project: str, env: str) -> List[Dict]:
        """List all roles in the database."""
        client = self.conn_manager.connect(project, env)

        query = """
        SELECT
            name,
            id,
            storage
        FROM system.roles
        ORDER BY name
        """

        result = client.query(query)
        roles = []
        for row in result.result_rows:
            roles.append({
                'name': row[0],
                'id': str(row[1]),
                'storage': row[2]
            })

        return roles

    def show_user_grants(self, project: str, env: str, username: str) -> List[str]:
        """Show all grants for a specific user."""
        client = self.conn_manager.connect(project, env)

        try:
            result = client.query(f"SHOW GRANTS FOR {username}")
            grants = [row[0] for row in result.result_rows]
            return grants
        except Exception as e:
            console.print(f"[red]Failed to get grants: {e}[/red]")
            return []

    def show_role_grants(self, project: str, env: str, role_name: str) -> List[str]:
        """Show all grants for a specific role."""
        client = self.conn_manager.connect(project, env)

        try:
            # Get grants directly assigned to the role
            query = """
            SELECT concat(
                'GRANT ', privilege, ' ON ',
                if(database = '', '*.*', concat(database, '.', table)),
                ' TO ', role_name
            ) as grant_statement
            FROM system.grants
            WHERE role_name = %(role)s
            """
            result = client.query(query, parameters={'role': role_name})
            grants = [row[0] for row in result.result_rows]
            return grants
        except Exception as e:
            console.print(f"[red]Failed to get role grants: {e}[/red]")
            return []

    def copy_user(
        self,
        project: str,
        from_env: str,
        to_env: str,
        username: str,
        new_password: Optional[str] = None
    ):
        """Copy a user from one environment to another."""
        # Get user info from source
        from_client = self.conn_manager.connect(project, from_env)

        # Get user grants
        grants = self.show_user_grants(project, from_env, username)

        # Create user in target environment
        password = new_password or self.generate_password()
        self.create_user(project, to_env, username, password)

        # Apply grants (need to parse and adjust database names)
        to_client = self.conn_manager.connect(project, to_env)
        to_database = self.conn_manager.get_database_name(project, to_env)

        for grant in grants:
            # Skip the CREATE USER grant
            if 'CREATE USER' in grant:
                continue

            # Adjust database name in grant if needed
            # This is simplified - might need more sophisticated parsing
            try:
                to_client.command(grant)
                console.print(f"[dim]  Applied: {grant[:60]}...[/dim]")
            except Exception as e:
                console.print(f"[yellow]  Warning: Could not apply grant: {e}[/yellow]")

        console.print(f"[green]✓ User '{username}' copied from {from_env} to {to_env}[/green]")

    def sync_users(self, project: str, from_env: str, to_env: str, users: Optional[List[str]] = None):
        """Sync multiple users from one environment to another."""
        if not users:
            # Get all users from source environment
            source_users = self.list_users(project, from_env)
            users = [u['name'] for u in source_users if not u['name'].startswith('default')]

        console.print(f"[cyan]Syncing {len(users)} users from {from_env} to {to_env}...[/cyan]")

        for username in users:
            try:
                self.copy_user(project, from_env, to_env, username)
            except Exception as e:
                console.print(f"[red]Failed to sync user '{username}': {e}[/red]")

    def display_users_table(self, project: str, env: str):
        """Display a formatted table of users."""
        users = self.list_users(project, env)

        table = Table(title=f"Users in {project}/{env}")
        table.add_column("Username", style="cyan")
        table.add_column("Auth Type", style="yellow")
        table.add_column("Default Roles", style="green")
        table.add_column("Host Restrictions", style="magenta")

        for user in users:
            host_info = []
            if user['host_names']:
                host_info.extend(user['host_names'])
            if user['host_ips']:
                host_info.extend(user['host_ips'])
            hosts = ', '.join(host_info) if host_info else "Any"

            roles = ', '.join(user['default_roles']) if user['default_roles'] else "None"

            table.add_row(
                user['name'],
                user['auth_type'] or 'default',
                roles,
                hosts
            )

        console.print(table)

    def display_roles_table(self, project: str, env: str):
        """Display a formatted table of roles."""
        roles = self.list_roles(project, env)

        table = Table(title=f"Roles in {project}/{env}")
        table.add_column("Role Name", style="cyan")
        table.add_column("Storage", style="yellow")
        table.add_column("ID", style="dim")

        for role in roles:
            table.add_row(
                role['name'],
                role['storage'],
                role['id']
            )

        console.print(table)

    def interactive_user_creation(self, project: str, env: str):
        """Interactive wizard for creating a new user."""
        console.print("[bold cyan]Create New User[/bold cyan]")

        username = Prompt.ask("Username")

        # Ask about password
        if Confirm.ask("Generate password automatically?", default=True):
            password = None
        else:
            password = Prompt.ask("Password", password=True)

        # Ask about role
        console.print("\n[cyan]Available role templates:[/cyan]")
        for key, template in self.ROLE_TEMPLATES.items():
            console.print(f"  [yellow]{key}[/yellow]: {template['description']}")

        role_choice = Prompt.ask(
            "Select role template",
            choices=list(self.ROLE_TEMPLATES.keys()) + ['custom', 'none'],
            default='service'
        )

        # Create user
        generated_password = self.create_user(project, env, username, password)

        # Create and assign role if selected
        if role_choice != 'none':
            if role_choice == 'custom':
                role_name = Prompt.ask("Custom role name")
                self.create_role(project, env, role_name)
            else:
                role_name = f"{username}_{role_choice}_role"
                self.create_role(project, env, role_name, template=role_choice)

            self.grant_role(project, env, username, role_name)

        console.print(f"\n[green]✓ User setup complete![/green]")
        if generated_password:
            console.print(f"[yellow]Password: {generated_password}[/yellow]")
            console.print("[dim]Please save this password securely![/dim]")


# Convenience functions
def quick_create_user(
    project: str,
    env: str,
    username: str,
    role_template: str = 'service'
) -> str:
    """Quick function to create a user with a standard role."""
    manager = UserManager()

    # Create user
    password = manager.create_user(project, env, username)

    # Create role based on template
    role_name = f"{username}_{role_template}_role"
    manager.create_role(project, env, role_name, template=role_template)

    # Grant role
    manager.grant_role(project, env, username, role_name)

    return password
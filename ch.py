#!/usr/bin/env python3
"""
ClickHouse Tools CLI
Main command-line interface for managing multiple ClickHouse projects and environments.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional
import click
import yaml
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from rich.prompt import Prompt, Confirm
from tabulate import tabulate

from connection import ConnectionManager, get_default_connection
from users import UserManager

console = Console()


@click.group()
@click.pass_context
def cli(ctx):
    """ClickHouse Tools - Manage multiple ClickHouse projects and environments."""
    ctx.ensure_object(dict)
    ctx.obj['conn_manager'] = ConnectionManager()
    ctx.obj['user_manager'] = UserManager(ctx.obj['conn_manager'])


@cli.command()
@click.pass_context
def list(ctx):
    """List all configured projects and environments."""
    conn_manager = ctx.obj['conn_manager']
    conn_manager.show_all_connections()


@cli.command()
@click.argument('project')
@click.argument('env')
@click.option('--client', default='clickhouse-client', help='ClickHouse client command')
@click.pass_context
def connect(ctx, project, env, client):
    """Connect to a ClickHouse instance using the native client."""
    conn_manager = ctx.obj['conn_manager']

    # Get connection info
    try:
        info = conn_manager.get_connection_info(project, env)
        username, password = conn_manager._get_credentials(project, env)

        # Build clickhouse-client command
        cmd = [
            client,
            '--host', info['host'],
            '--port', str(info['port']),
            '--database', info['database'],
            '--user', username,
            '--password', password
        ]

        if info.get('secure', True):
            cmd.append('--secure')

        console.print(f"[green]Connecting to {project}/{env}...[/green]")
        subprocess.run(cmd)

    except Exception as e:
        console.print(f"[red]Failed to connect: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('project')
@click.argument('env')
@click.argument('query', required=False)
@click.option('--file', '-f', help='Execute query from file')
@click.option('--format', default='Pretty', help='Output format (Pretty, TabSeparated, JSON, etc.)')
@click.pass_context
def query(ctx, project, env, query, file, format):
    """Execute a query on a ClickHouse instance."""
    conn_manager = ctx.obj['conn_manager']

    if not query and not file:
        console.print("[red]Either provide a query or use --file option[/red]")
        sys.exit(1)

    try:
        if file:
            result = conn_manager.execute_file(project, env, file)
            console.print(f"[green]Executed query from {file}[/green]")
        else:
            result = conn_manager.execute_query(project, env, query)

        # Display results
        if result and hasattr(result, 'result_rows') and result.result_rows:
            if format == 'Pretty':
                # Use rich table for pretty output
                table = Table()

                # Add columns
                if hasattr(result, 'column_names'):
                    for col in result.column_names:
                        table.add_column(col)

                # Add rows
                for row in result.result_rows:
                    table.add_row(*[str(val) for val in row])

                console.print(table)
            else:
                # Use tabulate for other formats
                if hasattr(result, 'column_names'):
                    print(tabulate(result.result_rows, headers=result.column_names, tablefmt='grid'))
                else:
                    for row in result.result_rows:
                        print('\t'.join(str(val) for val in row))
        else:
            console.print("[green]Query executed successfully[/green]")

    except Exception as e:
        console.print(f"[red]Query failed: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('project')
@click.argument('env')
@click.argument('file_path')
@click.pass_context
def exec(ctx, project, env, file_path):
    """Execute SQL from a file."""
    conn_manager = ctx.obj['conn_manager']

    path = Path(file_path)
    if not path.exists():
        # Try looking in queries directory
        queries_path = Path('queries') / file_path
        if queries_path.exists():
            path = queries_path
        else:
            console.print(f"[red]File not found: {file_path}[/red]")
            sys.exit(1)

    try:
        console.print(f"[cyan]Executing {path}...[/cyan]")

        # Show the SQL being executed
        with open(path, 'r') as f:
            sql_content = f.read()
            syntax = Syntax(sql_content, "sql", theme="monokai", line_numbers=True)
            console.print(syntax)

        if Confirm.ask("Execute this SQL?", default=True):
            result = conn_manager.execute_file(project, env, str(path))
            console.print(f"[green]✓ Executed successfully[/green]")

            # Show results if any
            if result and hasattr(result, 'result_rows') and result.result_rows:
                table = Table()
                if hasattr(result, 'column_names'):
                    for col in result.column_names:
                        table.add_column(col)
                for row in result.result_rows[:10]:  # Limit to first 10 rows
                    table.add_row(*[str(val) for val in row])
                console.print(table)
                if len(result.result_rows) > 10:
                    console.print(f"[dim]... and {len(result.result_rows) - 10} more rows[/dim]")

    except Exception as e:
        console.print(f"[red]Execution failed: {e}[/red]")
        sys.exit(1)


# User management commands
@cli.group()
def user():
    """User management commands."""
    pass


@user.command('create')
@click.argument('project')
@click.argument('env')
@click.argument('username')
@click.option('--role', default='service', help='Role template to use')
@click.option('--password', help='User password (generated if not provided)')
@click.pass_context
def user_create(ctx, project, env, username, role, password):
    """Create a new user."""
    user_manager = ctx.obj['user_manager']

    try:
        # Create user
        generated_password = user_manager.create_user(project, env, username, password)

        # Create and assign role
        if role != 'none':
            role_name = f"{username}_{role}_role"
            user_manager.create_role(project, env, role_name, template=role)
            user_manager.grant_role(project, env, username, role_name)

        if generated_password and not password:
            console.print(f"\n[yellow]Generated password: {generated_password}[/yellow]")
            console.print("[dim]Save this password securely - it cannot be recovered![/dim]")

    except Exception as e:
        console.print(f"[red]Failed to create user: {e}[/red]")
        sys.exit(1)


@user.command('list')
@click.argument('project')
@click.argument('env')
@click.pass_context
def user_list(ctx, project, env):
    """List all users."""
    user_manager = ctx.obj['user_manager']
    user_manager.display_users_table(project, env)


@user.command('show')
@click.argument('project')
@click.argument('env')
@click.argument('username')
@click.pass_context
def user_show(ctx, project, env, username):
    """Show user details and permissions."""
    user_manager = ctx.obj['user_manager']

    try:
        grants = user_manager.show_user_grants(project, env, username)

        console.print(f"\n[bold cyan]User: {username}[/bold cyan]")
        console.print(f"[dim]Project: {project} / Environment: {env}[/dim]\n")

        if grants:
            console.print("[yellow]Grants:[/yellow]")
            for grant in grants:
                console.print(f"  • {grant}")
        else:
            console.print("[dim]No grants found[/dim]")

    except Exception as e:
        console.print(f"[red]Failed to show user: {e}[/red]")
        sys.exit(1)


@user.command('copy')
@click.argument('project')
@click.argument('username')
@click.option('--from', 'from_env', required=True, help='Source environment')
@click.option('--to', 'to_env', required=True, help='Target environment')
@click.pass_context
def user_copy(ctx, project, username, from_env, to_env):
    """Copy a user from one environment to another."""
    user_manager = ctx.obj['user_manager']

    try:
        user_manager.copy_user(project, from_env, to_env, username)
    except Exception as e:
        console.print(f"[red]Failed to copy user: {e}[/red]")
        sys.exit(1)


@user.command('sync')
@click.argument('project')
@click.option('--from', 'from_env', required=True, help='Source environment')
@click.option('--to', 'to_env', required=True, help='Target environment')
@click.option('--users', help='Comma-separated list of users to sync (all if not specified)')
@click.pass_context
def user_sync(ctx, project, from_env, to_env, users):
    """Sync users from one environment to another."""
    user_manager = ctx.obj['user_manager']

    user_list = users.split(',') if users else None

    if not users:
        if not Confirm.ask(f"Sync ALL users from {from_env} to {to_env}?", default=False):
            return

    try:
        user_manager.sync_users(project, from_env, to_env, user_list)
    except Exception as e:
        console.print(f"[red]Sync failed: {e}[/red]")
        sys.exit(1)


# Role management commands
@cli.group()
def role():
    """Role management commands."""
    pass


@role.command('list')
@click.argument('project')
@click.argument('env')
@click.pass_context
def role_list(ctx, project, env):
    """List all roles."""
    user_manager = ctx.obj['user_manager']
    user_manager.display_roles_table(project, env)


@role.command('create')
@click.argument('project')
@click.argument('env')
@click.argument('role_name')
@click.option('--template', help='Role template to use')
@click.pass_context
def role_create(ctx, project, env, role_name, template):
    """Create a new role."""
    user_manager = ctx.obj['user_manager']

    try:
        user_manager.create_role(project, env, role_name, template=template)
    except Exception as e:
        console.print(f"[red]Failed to create role: {e}[/red]")
        sys.exit(1)


@role.command('show')
@click.argument('project')
@click.argument('env')
@click.argument('role_name')
@click.pass_context
def role_show(ctx, project, env, role_name):
    """Show role permissions."""
    user_manager = ctx.obj['user_manager']

    try:
        grants = user_manager.show_role_grants(project, env, role_name)

        console.print(f"\n[bold cyan]Role: {role_name}[/bold cyan]")
        console.print(f"[dim]Project: {project} / Environment: {env}[/dim]\n")

        if grants:
            console.print("[yellow]Grants:[/yellow]")
            for grant in grants:
                console.print(f"  • {grant}")
        else:
            console.print("[dim]No grants found[/dim]")

    except Exception as e:
        console.print(f"[red]Failed to show role: {e}[/red]")
        sys.exit(1)


# Test connection command
@cli.command()
@click.argument('project', required=False)
@click.argument('env', required=False)
@click.option('--all', 'test_all', is_flag=True, help='Test all configured connections')
@click.pass_context
def test(ctx, project, env, test_all):
    """Test database connections."""
    conn_manager = ctx.obj['conn_manager']

    if test_all:
        console.print("[cyan]Testing all connections...[/cyan]\n")

        success_count = 0
        fail_count = 0

        for proj in conn_manager.list_projects():
            for environment in conn_manager.list_environments(proj):
                if conn_manager.test_connection(proj, environment):
                    console.print(f"✓ {proj}/{environment}: [green]Connected[/green]")
                    success_count += 1
                else:
                    console.print(f"✗ {proj}/{environment}: [red]Failed[/red]")
                    fail_count += 1

        console.print(f"\n[cyan]Results: {success_count} successful, {fail_count} failed[/cyan]")

    else:
        if not project or not env:
            default_project, default_env = get_default_connection()
            project = project or default_project
            env = env or default_env

        if not project or not env:
            console.print("[red]Specify project and environment or use --all[/red]")
            sys.exit(1)

        if conn_manager.test_connection(project, env):
            console.print(f"[green]✓ Successfully connected to {project}/{env}[/green]")
        else:
            console.print(f"[red]✗ Failed to connect to {project}/{env}[/red]")
            sys.exit(1)


# Configuration commands
@cli.group()
def config():
    """Configuration management commands."""
    pass


@config.command('show')
@click.pass_context
def config_show(ctx):
    """Show current configuration."""
    config_path = Path("projects.yaml")
    if not config_path.exists():
        console.print("[red]Configuration file not found[/red]")
        sys.exit(1)

    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    syntax = Syntax(yaml.dump(config, default_flow_style=False), "yaml", theme="monokai")
    console.print(syntax)


@config.command('edit')
@click.pass_context
def config_edit(ctx):
    """Open configuration file in editor."""
    config_path = Path("projects.yaml")
    editor = os.environ.get('EDITOR', 'nano')

    subprocess.run([editor, str(config_path)])


@config.command('validate')
@click.pass_context
def config_validate(ctx):
    """Validate configuration file."""
    try:
        conn_manager = ConnectionManager()
        console.print("[green]✓ Configuration file is valid[/green]")

        # Show summary
        projects = conn_manager.list_projects()
        console.print(f"\n[cyan]Found {len(projects)} project(s):[/cyan]")
        for project in projects:
            envs = conn_manager.list_environments(project)
            console.print(f"  • {project}: {', '.join(envs)}")

    except Exception as e:
        console.print(f"[red]✗ Configuration validation failed: {e}[/red]")
        sys.exit(1)


# Initialize new project
@cli.command()
@click.argument('project_name')
@click.option('--environments', '-e', default='dev,staging,prod', help='Comma-separated environments')
@click.pass_context
def init(ctx, project_name, environments):
    """Initialize a new ClickHouse project."""
    config_path = Path("projects.yaml")

    # Load existing config or create new
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    else:
        config = {
            'projects': {},
            'settings': {
                'default_project': project_name,
                'default_environment': 'dev',
                'connection_timeout': 10,
                'credential_storage': 'env'
            }
        }

    # Check if project already exists
    if project_name in config.get('projects', {}):
        console.print(f"[yellow]Project '{project_name}' already exists[/yellow]")
        if not Confirm.ask("Overwrite?", default=False):
            return

    # Create project structure
    envs = [e.strip() for e in environments.split(',')]
    project_config = {
        'description': Prompt.ask(f"Project description", default=f"{project_name} database"),
        'environments': {}
    }

    for env in envs:
        console.print(f"\n[cyan]Configure {env} environment:[/cyan]")
        host = Prompt.ask(f"  Host", default=f"{project_name}-{env}.clickhouse.cloud")
        database = Prompt.ask(f"  Database", default=f"{project_name}_{env}" if env != 'prod' else project_name)

        project_config['environments'][env] = {
            'host': host,
            'port': 8443,
            'database': database,
            'secure': True
        }

    config['projects'][project_name] = project_config

    # Save configuration
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    console.print(f"\n[green]✓ Project '{project_name}' initialized successfully![/green]")
    console.print("\n[cyan]Next steps:[/cyan]")
    console.print(f"1. Set credentials in environment variables or .env file")
    console.print(f"2. Test connection: ch test {project_name} dev")
    console.print(f"3. Create users: ch user create {project_name} dev <username>")


if __name__ == '__main__':
    cli()
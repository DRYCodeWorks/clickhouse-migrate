#!/usr/bin/env python3
"""
Sync users between ClickHouse environments.
Useful for promoting user configurations from dev to staging/production.
"""

import click
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm
from connection import ConnectionManager
from users import UserManager

console = Console()


@click.command()
@click.argument('project')
@click.argument('from_env')
@click.argument('to_env')
@click.option('--users', help='Comma-separated list of users to sync')
@click.option('--dry-run', is_flag=True, help='Show what would be synced without making changes')
@click.option('--skip-system', is_flag=True, default=True, help='Skip system users (default, clickhouse)')
def sync_users(project, from_env, to_env, users, dry_run, skip_system):
    """
    Sync users from one ClickHouse environment to another.

    Example:
        python sync_users.py metopio dev staging
        python sync_users.py metopio dev prod --users=user1,user2
        python sync_users.py metopio staging prod --dry-run
    """
    conn_manager = ConnectionManager()
    user_manager = UserManager(conn_manager)

    console.print(f"[cyan]Syncing users from {project}/{from_env} to {project}/{to_env}[/cyan]\n")

    # Get users from source environment
    source_users = user_manager.list_users(project, from_env)
    target_users = user_manager.list_users(project, to_env)

    # Filter users
    if users:
        user_list = [u.strip() for u in users.split(',')]
        source_users = [u for u in source_users if u['name'] in user_list]
    elif skip_system:
        system_users = ['default', 'clickhouse', 'play']
        source_users = [u for u in source_users if u['name'] not in system_users]

    # Get existing users in target
    target_usernames = {u['name'] for u in target_users}

    # Prepare sync plan
    to_create = []
    to_update = []
    to_skip = []

    for user in source_users:
        username = user['name']
        if username in target_usernames:
            to_update.append(username)
        else:
            to_create.append(username)

    # Display sync plan
    console.print("[bold]Sync Plan:[/bold]\n")

    if to_create:
        table = Table(title="Users to Create", style="green")
        table.add_column("Username")
        for username in to_create:
            table.add_row(username)
        console.print(table)
        console.print()

    if to_update:
        table = Table(title="Users to Update (Re-sync permissions)", style="yellow")
        table.add_column("Username")
        for username in to_update:
            table.add_row(username)
        console.print(table)
        console.print()

    if not to_create and not to_update:
        console.print("[dim]No users to sync[/dim]")
        return

    # Confirm or execute
    if dry_run:
        console.print("[dim]Dry run mode - no changes made[/dim]")
        return

    if not Confirm.ask("\nProceed with sync?", default=False):
        console.print("[yellow]Sync cancelled[/yellow]")
        return

    # Execute sync
    console.print("\n[cyan]Executing sync...[/cyan]\n")

    success_count = 0
    fail_count = 0

    for username in to_create + to_update:
        try:
            # Get user grants from source
            grants = user_manager.show_user_grants(project, from_env, username)

            if username in to_create:
                # Create new user
                console.print(f"Creating user: {username}")
                password = user_manager.create_user(project, to_env, username)
                console.print(f"  [green]✓[/green] User created")

                # Apply grants
                client = conn_manager.connect(project, to_env)
                for grant in grants:
                    if 'CREATE USER' not in grant:
                        try:
                            client.command(grant.replace(from_env, to_env))
                        except:
                            pass  # Some grants might not apply

            else:
                # Update existing user's permissions
                console.print(f"Updating permissions for: {username}")
                client = conn_manager.connect(project, to_env)

                # Revoke all current grants first (optional)
                # client.command(f"REVOKE ALL ON *.* FROM {username}")

                # Apply grants from source
                for grant in grants:
                    if 'CREATE USER' not in grant:
                        try:
                            client.command(grant.replace(from_env, to_env))
                        except:
                            pass

                console.print(f"  [green]✓[/green] Permissions updated")

            success_count += 1

        except Exception as e:
            console.print(f"  [red]✗[/red] Failed: {e}")
            fail_count += 1

    # Summary
    console.print(f"\n[bold]Sync Complete:[/bold]")
    console.print(f"  [green]✓ Successful: {success_count}[/green]")
    if fail_count > 0:
        console.print(f"  [red]✗ Failed: {fail_count}[/red]")


if __name__ == '__main__':
    sync_users()
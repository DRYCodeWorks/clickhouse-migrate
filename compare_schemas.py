#!/usr/bin/env python3
"""
Compare table schemas between ClickHouse environments.
Useful for ensuring consistency across dev/staging/production.
"""

import click
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from connection import ConnectionManager
from typing import Dict, List, Set

console = Console()


def get_tables(conn_manager: ConnectionManager, project: str, env: str) -> List[str]:
    """Get list of tables in a database."""
    query = """
    SELECT name
    FROM system.tables
    WHERE database = currentDatabase()
        AND engine NOT IN ('View', 'MaterializedView', 'Dictionary')
    ORDER BY name
    """
    result = conn_manager.execute_query(project, env, query)
    return [row[0] for row in result.result_rows]


def get_table_schema(conn_manager: ConnectionManager, project: str, env: str, table: str) -> Dict:
    """Get detailed schema for a table."""
    # Get columns
    columns_query = """
    SELECT
        name,
        type,
        default_kind,
        default_expression,
        comment,
        codec_expression,
        ttl_expression
    FROM system.columns
    WHERE database = currentDatabase() AND table = %(table)s
    ORDER BY position
    """
    columns_result = conn_manager.execute_query(project, env, columns_query, {'table': table})

    # Get CREATE TABLE statement
    create_query = f"SHOW CREATE TABLE {table}"
    create_result = conn_manager.execute_query(project, env, create_query)
    create_statement = create_result.result_rows[0][0] if create_result.result_rows else ""

    # Get table engine and settings
    engine_query = """
    SELECT
        engine,
        partition_key,
        sorting_key,
        primary_key,
        sampling_key,
        storage_policy
    FROM system.tables
    WHERE database = currentDatabase() AND name = %(table)s
    """
    engine_result = conn_manager.execute_query(project, env, engine_query, {'table': table})

    return {
        'columns': [
            {
                'name': row[0],
                'type': row[1],
                'default_kind': row[2],
                'default_expression': row[3],
                'comment': row[4],
                'codec': row[5],
                'ttl': row[6]
            }
            for row in columns_result.result_rows
        ],
        'create_statement': create_statement,
        'engine': engine_result.result_rows[0] if engine_result.result_rows else None
    }


def compare_columns(cols1: List[Dict], cols2: List[Dict]) -> Dict:
    """Compare column definitions between two schemas."""
    cols1_map = {col['name']: col for col in cols1}
    cols2_map = {col['name']: col for col in cols2}

    cols1_names = set(cols1_map.keys())
    cols2_names = set(cols2_map.keys())

    differences = {
        'missing_in_target': cols1_names - cols2_names,
        'extra_in_target': cols2_names - cols1_names,
        'type_differences': [],
        'other_differences': []
    }

    # Check for type and other differences
    common_columns = cols1_names & cols2_names
    for col_name in common_columns:
        col1 = cols1_map[col_name]
        col2 = cols2_map[col_name]

        if col1['type'] != col2['type']:
            differences['type_differences'].append({
                'column': col_name,
                'source_type': col1['type'],
                'target_type': col2['type']
            })

        # Check other properties
        for prop in ['default_kind', 'default_expression', 'codec', 'ttl']:
            if col1.get(prop) != col2.get(prop):
                differences['other_differences'].append({
                    'column': col_name,
                    'property': prop,
                    'source_value': col1.get(prop),
                    'target_value': col2.get(prop)
                })

    return differences


@click.command()
@click.argument('project')
@click.argument('env1')
@click.argument('env2')
@click.option('--table', help='Compare specific table only')
@click.option('--verbose', is_flag=True, help='Show detailed differences')
@click.option('--show-create', is_flag=True, help='Show CREATE TABLE statements')
def compare_schemas(project, env1, env2, table, verbose, show_create):
    """
    Compare table schemas between two ClickHouse environments.

    Examples:
        python compare_schemas.py metopio dev prod
        python compare_schemas.py metopio dev staging --table users
        python compare_schemas.py metopio staging prod --verbose
    """
    conn_manager = ConnectionManager()

    console.print(f"[cyan]Comparing schemas: {project}/{env1} vs {project}/{env2}[/cyan]\n")

    # Get tables from both environments
    if table:
        tables1 = [table]
        tables2 = [table]
    else:
        console.print("Fetching table lists...")
        tables1 = get_tables(conn_manager, project, env1)
        tables2 = get_tables(conn_manager, project, env2)

    tables1_set = set(tables1)
    tables2_set = set(tables2)

    # Find table differences
    missing_in_env2 = tables1_set - tables2_set
    extra_in_env2 = tables2_set - tables1_set
    common_tables = tables1_set & tables2_set

    # Display table-level differences
    if missing_in_env2:
        table_missing = Table(title=f"Tables missing in {env2}", style="red")
        table_missing.add_column("Table Name")
        for t in sorted(missing_in_env2):
            table_missing.add_row(t)
        console.print(table_missing)
        console.print()

    if extra_in_env2:
        table_extra = Table(title=f"Extra tables in {env2}", style="yellow")
        table_extra.add_column("Table Name")
        for t in sorted(extra_in_env2):
            table_extra.add_row(t)
        console.print(table_extra)
        console.print()

    # Compare schemas for common tables
    if common_tables:
        console.print(f"[cyan]Comparing {len(common_tables)} common tables...[/cyan]\n")

        differences_found = False

        for table_name in sorted(common_tables):
            schema1 = get_table_schema(conn_manager, project, env1, table_name)
            schema2 = get_table_schema(conn_manager, project, env2, table_name)

            col_diff = compare_columns(schema1['columns'], schema2['columns'])

            # Check if there are any differences
            has_differences = (
                col_diff['missing_in_target'] or
                col_diff['extra_in_target'] or
                col_diff['type_differences'] or
                (verbose and col_diff['other_differences'])
            )

            if has_differences:
                differences_found = True
                console.print(f"[bold yellow]Table: {table_name}[/bold yellow]")

                if col_diff['missing_in_target']:
                    console.print(f"  [red]Missing columns in {env2}:[/red]")
                    for col in col_diff['missing_in_target']:
                        console.print(f"    - {col}")

                if col_diff['extra_in_target']:
                    console.print(f"  [yellow]Extra columns in {env2}:[/yellow]")
                    for col in col_diff['extra_in_target']:
                        console.print(f"    + {col}")

                if col_diff['type_differences']:
                    console.print(f"  [magenta]Type differences:[/magenta]")
                    for diff in col_diff['type_differences']:
                        console.print(
                            f"    • {diff['column']}: "
                            f"{diff['source_type']} ({env1}) → "
                            f"{diff['target_type']} ({env2})"
                        )

                if verbose and col_diff['other_differences']:
                    console.print(f"  [dim]Other differences:[/dim]")
                    for diff in col_diff['other_differences']:
                        console.print(
                            f"    • {diff['column']}.{diff['property']}: "
                            f"{diff['source_value']} → {diff['target_value']}"
                        )

                # Show CREATE statements if requested
                if show_create:
                    console.print(f"\n  [dim]CREATE TABLE statement in {env1}:[/dim]")
                    syntax1 = Syntax(schema1['create_statement'], "sql", theme="monokai")
                    console.print(syntax1)

                    console.print(f"\n  [dim]CREATE TABLE statement in {env2}:[/dim]")
                    syntax2 = Syntax(schema2['create_statement'], "sql", theme="monokai")
                    console.print(syntax2)

                console.print()

        if not differences_found:
            console.print("[green]✓ All common tables have identical schemas![/green]")
    else:
        console.print("[yellow]No common tables to compare[/yellow]")

    # Summary
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"  Tables in {env1}: {len(tables1_set)}")
    console.print(f"  Tables in {env2}: {len(tables2_set)}")
    console.print(f"  Common tables: {len(common_tables)}")
    if missing_in_env2:
        console.print(f"  [red]Missing in {env2}: {len(missing_in_env2)}[/red]")
    if extra_in_env2:
        console.print(f"  [yellow]Extra in {env2}: {len(extra_in_env2)}[/yellow]")


if __name__ == '__main__':
    compare_schemas()
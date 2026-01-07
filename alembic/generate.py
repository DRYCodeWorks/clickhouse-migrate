#!/usr/bin/env python3
"""
Migration generator for ClickHouse migrations.

This script provides utilities to generate common ClickHouse migration patterns
from templates, making it easier to create well-structured migrations.

Author: Dan Young
License: MIT License
Copyright (c) 2025 Dan Young
"""

import typer
from pathlib import Path
from datetime import datetime
import uuid
import re

app = typer.Typer(help="ClickHouse Migration Generator")


def generate_revision_id():
    """Generate a short revision ID similar to Alembic's style"""
    return str(uuid.uuid4()).replace('-', '')[:12]


def format_table_name(name: str) -> str:
    """Format table name to be ClickHouse-friendly"""
    # Convert to snake_case and remove invalid characters
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name).lower()
    name = re.sub(r'_+', '_', name).strip('_')
    return name


def get_next_migration_number():
    """Get the next migration number based on existing files"""
    migration_dir = Path("clickhouse_migrations")
    if not migration_dir.exists():
        migration_dir.mkdir(parents=True)
    
    existing_files = list(migration_dir.glob("*.py"))
    if not existing_files:
        return 1
    
    # Extract numbers from existing migration files
    numbers = []
    for file in existing_files:
        if file.name.startswith(('1', '2', '3', '4', '5', '6', '7', '8', '9')):
            try:
                # Extract the first number from the filename
                first_part = file.name.split('_')[0]
                if first_part.isdigit():
                    numbers.append(int(first_part))
            except (ValueError, IndexError):
                continue
    
    return max(numbers, default=0) + 1 if numbers else 1


@app.command()
def table(
    name: str = typer.Argument(help="Table name"),
    message: str = typer.Option(None, "--message", "-m", help="Migration message"),
    template: str = typer.Option("table_migration.py.template", help="Template file to use")
):
    """Generate a table creation migration"""
    
    table_name = format_table_name(name)
    template_path = Path("templates") / template
    
    if not template_path.exists():
        typer.echo(f"❌ Template not found: {template_path}")
        typer.echo("Available templates:")
        for tmpl in Path("templates").glob("*.template"):
            typer.echo(f"  - {tmpl.name}")
        raise typer.Exit(1)
    
    # Generate migration details
    revision = generate_revision_id()
    create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    migration_message = message or f"create_{table_name}_table"
    
    # Read template
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    # Replace template variables
    migration_content = template_content.format(
        table_name=table_name,
        revision=revision,
        down_revision="None",  # Will be updated by user or alembic
        branch_labels="None",
        depends_on="None",
        create_date=create_date
    )
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y_%m_%d_%H%M")
    filename = f"{timestamp}_{migration_message}.py"
    output_path = Path("clickhouse_migrations") / filename
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write migration file
    with open(output_path, 'w') as f:
        f.write(migration_content)
    
    typer.echo(f"✅ Generated table migration: {output_path}")
    typer.echo(f"📝 Table name: {table_name}")
    typer.echo(f"🔗 Revision ID: {revision}")


@app.command()
def view(
    name: str = typer.Argument(help="Materialized view name"),
    message: str = typer.Option(None, "--message", "-m", help="Migration message"),
    template: str = typer.Option("materialized_view_migration.py.template", help="Template file to use")
):
    """Generate a materialized view migration"""
    
    view_name = format_table_name(name)
    template_path = Path("templates") / template
    
    if not template_path.exists():
        typer.echo(f"❌ Template not found: {template_path}")
        raise typer.Exit(1)
    
    # Generate migration details
    revision = generate_revision_id()
    create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    migration_message = message or f"create_{view_name}_materialized_view"
    
    # Read and process template
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    migration_content = template_content.format(
        view_name=view_name,
        revision=revision,
        down_revision="None",
        branch_labels="None", 
        depends_on="None",
        create_date=create_date
    )
    
    # Generate filename and write
    timestamp = datetime.now().strftime("%Y_%m_%d_%H%M")
    filename = f"{timestamp}_{migration_message}.py"
    output_path = Path("clickhouse_migrations") / filename
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(migration_content)
    
    typer.echo(f"✅ Generated materialized view migration: {output_path}")
    typer.echo(f"📝 View name: {view_name}")
    typer.echo(f"🔗 Revision ID: {revision}")


@app.command()
def dictionary(
    name: str = typer.Argument(help="Dictionary name"),
    message: str = typer.Option(None, "--message", "-m", help="Migration message"),
    template: str = typer.Option("dictionary_migration.py.template", help="Template file to use")
):
    """Generate a dictionary migration"""
    
    dict_name = format_table_name(name)
    template_path = Path("templates") / template
    
    if not template_path.exists():
        typer.echo(f"❌ Template not found: {template_path}")
        raise typer.Exit(1)
    
    # Generate migration details
    revision = generate_revision_id()
    create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    migration_message = message or f"create_{dict_name}_dictionary"
    
    # Read and process template
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    migration_content = template_content.format(
        dictionary_name=dict_name,
        revision=revision,
        down_revision="None",
        branch_labels="None",
        depends_on="None", 
        create_date=create_date
    )
    
    # Generate filename and write
    timestamp = datetime.now().strftime("%Y_%m_%d_%H%M")
    filename = f"{timestamp}_{migration_message}.py"
    output_path = Path("clickhouse_migrations") / filename
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(migration_content)
    
    typer.echo(f"✅ Generated dictionary migration: {output_path}")
    typer.echo(f"📝 Dictionary name: {dict_name}")
    typer.echo(f"🔗 Revision ID: {revision}")


@app.command()
def list_templates():
    """List available migration templates"""
    templates_dir = Path("templates")
    
    if not templates_dir.exists():
        typer.echo("❌ Templates directory not found")
        raise typer.Exit(1)
    
    templates = list(templates_dir.glob("*.template"))
    
    if not templates:
        typer.echo("❌ No templates found in templates/ directory")
        raise typer.Exit(1)
    
    typer.echo("📋 Available migration templates:")
    for template in sorted(templates):
        typer.echo(f"  - {template.name}")
        
        # Read first few lines to show description
        try:
            with open(template, 'r') as f:
                lines = f.readlines()[:3]
                for line in lines:
                    if line.strip().startswith('"""') and 'Create' in line:
                        desc = line.strip().replace('"""', '').strip()
                        typer.echo(f"    {desc}")
                        break
        except Exception:
            pass


@app.command()
def custom(
    template: str = typer.Argument(help="Template filename"),
    name: str = typer.Argument(help="Object name"),
    message: str = typer.Option(None, "--message", "-m", help="Migration message")
):
    """Generate migration from custom template"""
    
    template_path = Path("templates") / template
    
    if not template_path.exists():
        typer.echo(f"❌ Template not found: {template_path}")
        raise typer.Exit(1)
    
    object_name = format_table_name(name)
    revision = generate_revision_id()
    create_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    migration_message = message or f"create_{object_name}"
    
    # Read template
    with open(template_path, 'r') as f:
        template_content = f.read()
    
    # Replace common template variables
    migration_content = template_content.format(
        name=object_name,
        object_name=object_name,
        table_name=object_name,
        view_name=object_name, 
        dictionary_name=object_name,
        revision=revision,
        down_revision="None",
        branch_labels="None",
        depends_on="None",
        create_date=create_date
    )
    
    # Generate filename and write
    timestamp = datetime.now().strftime("%Y_%m_%d_%H%M")
    filename = f"{timestamp}_{migration_message}.py"
    output_path = Path("clickhouse_migrations") / filename
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(migration_content)
    
    typer.echo(f"✅ Generated migration from {template}: {output_path}")
    typer.echo(f"📝 Object name: {object_name}")
    typer.echo(f"🔗 Revision ID: {revision}")


if __name__ == "__main__":
    app()
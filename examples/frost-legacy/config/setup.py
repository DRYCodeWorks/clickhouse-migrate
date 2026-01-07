#!/usr/bin/env python3
"""
Setup script for ClickHouse migration tool.

This script helps initialize a new project with the appropriate
configuration files and directory structure.

Author: Dan Young
License: MIT License
Copyright (c) 2025 Dan Young
"""

import shutil
import typer
from pathlib import Path
from typing import Optional

from config.manager import ConfigManager

app = typer.Typer(help="ClickHouse Migration Tool Setup")


@app.command()
def init(
    config_template: str = typer.Option(
        "simple-local",
        "--template", "-t",
        help="Configuration template to use (simple-local, aws-cloud)"
    ),
    project_name: str = typer.Option(
        None,
        "--name", "-n", 
        help="Project name (will prompt if not provided)"
    ),
    force: bool = typer.Option(
        False,
        "--force", "-f",
        help="Overwrite existing files"
    )
):
    """Initialize a new ClickHouse migration project"""
    
    # Get project name if not provided
    if not project_name:
        project_name = typer.prompt("Enter project name")
    
    project_path = Path.cwd()
    config_path = project_path / "config" / "config.yaml"
    
    # Check if already initialized
    if config_path.exists() and not force:
        typer.echo(f"❌ Project already initialized. Use --force to overwrite.")
        raise typer.Exit(1)
    
    # Create directory structure
    dirs_to_create = [
        "config",
        "clickhouse_migrations", 
        "schemas",
        "schemas/clickhouse_sql"
    ]
    
    for dir_path in dirs_to_create:
        (project_path / dir_path).mkdir(parents=True, exist_ok=True)
    
    # Copy template configuration
    template_path = Path(__file__).parent / "examples" / f"{config_template}.yaml"
    
    if not template_path.exists():
        typer.echo(f"❌ Template '{config_template}' not found.")
        typer.echo("Available templates:")
        examples_dir = Path(__file__).parent / "examples"
        for template_file in examples_dir.glob("*.yaml"):
            typer.echo(f"  - {template_file.stem}")
        raise typer.Exit(1)
    
    # Copy and customize template
    shutil.copy2(template_path, config_path)
    
    # Update project name in config
    import yaml
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    config['project']['name'] = project_name
    config['project']['description'] = f"{project_name} ClickHouse migrations"
    
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    typer.echo(f"✅ Initialized project '{project_name}' with template '{config_template}'")
    typer.echo(f"📁 Configuration file: {config_path}")
    
    # Generate alembic.ini
    generate_alembic_ini(project_path / "config.yaml")
    
    # Create basic schema file
    create_basic_schema(project_path)
    
    typer.echo("\n📋 Next steps:")
    typer.echo("1. Update config/config.yaml with your environment details")
    typer.echo("2. Set up your credentials (environment variables, AWS secrets, etc.)")
    typer.echo("3. Create your first migration: alembic -n local revision -m 'initial_setup'")


@app.command()  
def generate_config():
    """Generate alembic.ini from current config.yaml"""
    config_path = Path.cwd() / "config" / "config.yaml"
    
    if not config_path.exists():
        typer.echo("❌ config/config.yaml not found. Run 'setup init' first.")
        raise typer.Exit(1)
    
    generate_alembic_ini(config_path)
    typer.echo("✅ Generated alembic.ini from configuration")


def generate_alembic_ini(config_path: Path):
    """Generate alembic.ini file from configuration"""
    try:
        manager = ConfigManager(config_path)
        output_path = Path.cwd() / "alembic.ini"
        manager.generate_alembic_ini(output_path)
        typer.echo(f"📄 Generated: {output_path}")
    except Exception as e:
        typer.echo(f"❌ Failed to generate alembic.ini: {str(e)}")
        raise typer.Exit(1)


def create_basic_schema(project_path: Path):
    """Create a basic schema.py file"""
    schema_path = project_path / "schemas" / "schema.py"
    
    schema_content = '''"""
Base schema module for ClickHouse migrations.

This module contains the SQLAlchemy base and metadata setup.
Add your table definitions here or import them from other modules.
"""

from sqlalchemy.ext.declarative import declarative_base

# Create the base class for declarative models
Base = declarative_base()
metadata = Base.metadata

# Naming convention for indexes, constraints, etc.
metadata.naming_convention = {
    "ix": "%(column_0_label)s_ix",
    "uq": "uq_%(table_name)s_%(column_0_name)s", 
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# Example table definition (uncomment and modify as needed):
# from sqlalchemy import Column, Integer, String, DateTime
# 
# class ExampleTable(Base):
#     __tablename__ = 'example_table'
#     
#     id = Column(Integer, primary_key=True)
#     name = Column(String(100), nullable=False)
#     created_at = Column(DateTime, nullable=False)
'''
    
    with open(schema_path, 'w') as f:
        f.write(schema_content)
    
    typer.echo(f"📄 Created: {schema_path}")


@app.command()
def validate():
    """Validate current configuration"""
    config_path = Path.cwd() / "config" / "config.yaml" 
    
    if not config_path.exists():
        typer.echo("❌ config/config.yaml not found")
        raise typer.Exit(1)
    
    try:
        manager = ConfigManager(config_path)
        environments = manager.get_environment_list()
        
        typer.echo(f"✅ Configuration valid")
        typer.echo(f"📊 Found {len(environments)} environments: {', '.join(environments)}")
        
        # Test credential provider
        cred_type = manager.config.get("credentials", {}).get("type", "env_vars")
        typer.echo(f"🔑 Credential provider: {cred_type}")
        
        # Validate each environment can generate URL
        for env in environments:
            try:
                url = manager.generate_sqlalchemy_url(env)
                typer.echo(f"  ✅ {env}: Connection URL generated")
            except Exception as e:
                typer.echo(f"  ❌ {env}: {str(e)}")
        
    except Exception as e:
        typer.echo(f"❌ Configuration error: {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
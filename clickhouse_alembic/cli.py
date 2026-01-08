"""Command-line interface for clickhouse-alembic."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import click
from dotenv import load_dotenv

from clickhouse_alembic.config import get_env_config

# Load .env.local if it exists in the current directory
_env_local = Path.cwd() / ".env.local"
if _env_local.exists():
    load_dotenv(_env_local)


def get_template_path(name: str) -> Path:
    """Get path to a template file."""
    return Path(__file__).parent / "templates" / "project" / f"{name}.template"


def render_template(template_path: Path, **kwargs: str) -> str:
    """Render a template with substitutions."""
    content = template_path.read_text()
    for key, value in kwargs.items():
        content = content.replace(f"{{{key}}}", value)
    return content


def _run_alembic(environment: str, args: list[str]) -> None:
    """Run alembic with environment configuration."""
    config_path = Path.cwd() / "config.yaml"

    try:
        env_config = get_env_config(environment, config_path)
    except Exception as e:
        click.echo(f"Error loading config: {e}", err=True)
        sys.exit(1)

    # Set environment variables for alembic
    env = os.environ.copy()
    env["CH_DATABASE"] = env_config["database"]
    env["CH_HOST"] = env_config["host"]
    env["CH_PORT"] = str(env_config.get("port", 8443))
    env["CH_USER"] = env_config.get("migration_user") or env_config.get("user", "")
    env["CH_PASSWORD"] = env_config.get("password", "")
    env["CH_SECURE"] = "1" if env_config.get("secure", True) else "0"

    result = subprocess.run(
        ["alembic", "-n", environment] + args,
        env=env,
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )

    # Show output from alembic
    if result.stdout:
        click.echo(result.stdout)
    if result.stderr:
        click.echo(result.stderr, err=True)

    if result.returncode != 0:
        click.echo(f"Alembic command failed with exit code {result.returncode}", err=True)

    sys.exit(result.returncode)


@click.group()
@click.version_option()
def main() -> None:
    """ClickHouse migration tool built on Alembic.

    ch-migrate provides a unified CLI for managing ClickHouse database migrations.
    It handles project initialization, database bootstrapping, and running migrations.

    \b
    Quick start:
      ch-migrate init                    # Initialize a new project
      ch-migrate bootstrap dev           # Set up database and users
      ch-migrate up dev                  # Apply pending migrations
      ch-migrate status dev              # Check migration status
    """
    pass


@main.command()
@click.argument("path", default=".", type=click.Path())
@click.option("--name", "-n", default=None, help="Project name (defaults to directory name)")
def init(path: str, name: str | None) -> None:
    """Initialize a new ClickHouse migration project.

    Creates the project structure with config.yaml, migrate.sh, and migrations directory.
    """
    project_path = Path(path).resolve()

    if name is None:
        name = project_path.name

    # Normalize project name (replace spaces/hyphens with underscores for database names)
    safe_name = name.replace("-", "_").replace(" ", "_").lower()

    click.echo(f"Initializing ClickHouse migration project: {name}")
    click.echo(f"  Path: {project_path}")

    # Create directories
    project_path.mkdir(parents=True, exist_ok=True)
    (project_path / "migrations" / "sql" / "bootstrap").mkdir(parents=True, exist_ok=True)
    (project_path / "migrations" / "sql" / "history" / "tables").mkdir(parents=True, exist_ok=True)
    (project_path / "migrations" / "sql" / "history" / "views").mkdir(parents=True, exist_ok=True)
    (project_path / "migrations" / "sql" / "history" / "dictionaries").mkdir(
        parents=True, exist_ok=True
    )
    (project_path / "migrations" / "versions").mkdir(parents=True, exist_ok=True)

    # Copy/render templates
    templates = [
        ("alembic.ini", "alembic.ini"),
        ("config.yaml", "config.yaml"),
        ("env.local.example", ".env.local.example"),
        ("migrate.sh", "migrate.sh"),
        ("script.py.mako", "migrations/script.py.mako"),
    ]

    for template_name, output_name in templates:
        template_path = get_template_path(template_name)
        output_path = project_path / output_name

        if output_path.exists():
            click.echo(f"  Skipping {output_name} (already exists)")
            continue

        content = render_template(template_path, project_name=safe_name)
        output_path.write_text(content)
        click.echo(f"  Created {output_name}")

    # Make migrate.sh executable
    migrate_sh = project_path / "migrate.sh"
    if migrate_sh.exists():
        migrate_sh.chmod(0o755)

    # Copy env.py from package
    env_py_src = Path(__file__).parent / "env.py"
    env_py_dst = project_path / "migrations" / "env.py"
    if not env_py_dst.exists():
        shutil.copy(env_py_src, env_py_dst)
        click.echo("  Created migrations/env.py")

    # Create .gitignore
    gitignore_path = project_path / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text(".env.local\n__pycache__/\n*.pyc\n")
        click.echo("  Created .gitignore")

    click.echo("")
    click.echo("Project initialized! Next steps:")
    click.echo("")
    click.echo("  1. Edit config.yaml with your ClickHouse hosts")
    click.echo("  2. Copy .env.local.example to .env.local and add passwords")
    click.echo("  3. Run: ch-migrate bootstrap dev")
    click.echo("  4. Create your first migration: ch-migrate new dev create_users_table")


@main.command()
@click.argument("environment")
@click.option("--dry-run", is_flag=True, help="Show SQL without executing")
@click.option("--verbose", "-v", is_flag=True, help="Show SQL statements as they execute")
def bootstrap(environment: str, dry_run: bool, verbose: bool) -> None:
    """Initialize database and users for an environment.

    Creates the database, roles, and users (migration user, optional MCP user,
    optional dict_reader user). Safe to run multiple times (idempotent).

    Requires admin credentials in .env.local or SSM.
    """
    from clickhouse_alembic.bootstrap import run_bootstrap

    try:
        run_bootstrap(environment, dry_run=dry_run, verbose=verbose)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("environment")
def up(environment: str) -> None:
    """Apply pending migrations.

    Runs all unapplied migrations to bring the database to the latest version.
    """
    _run_alembic(environment, ["upgrade", "head"])


@main.command()
@click.argument("environment")
@click.option("--revision", "-r", default="-1", help="Revision to downgrade to (default: -1)")
def down(environment: str, revision: str) -> None:
    """Rollback migrations.

    By default, rolls back the last migration. Use --revision to specify a target.
    """
    _run_alembic(environment, ["downgrade", revision])


@main.command()
@click.argument("environment")
def status(environment: str) -> None:
    """Show migration status.

    Displays the current revision and any pending migrations.
    """
    _run_alembic(environment, ["current", "-v"])


@main.command()
@click.argument("environment")
def history(environment: str) -> None:
    """Show migration history.

    Lists all migrations with their revision IDs and descriptions.
    """
    _run_alembic(environment, ["history", "-v"])


@main.command()
@click.argument("environment")
@click.argument("name")
def new(environment: str, name: str) -> None:
    """Create a new migration.

    Creates a new migration file with the given name. Edit the generated file
    to add your upgrade() and downgrade() logic.
    """
    _run_alembic(environment, ["revision", "-m", name])


if __name__ == "__main__":
    main()

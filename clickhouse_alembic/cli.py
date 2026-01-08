"""Command-line interface for clickhouse-alembic."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
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


def _run_alembic(
    environment: str, args: list[str], *, exit_on_complete: bool = True
) -> subprocess.CompletedProcess[str] | None:
    """Run alembic with environment configuration.

    Args:
        environment: Environment name (dev, staging, production)
        args: Arguments to pass to alembic
        exit_on_complete: If True, exit after running. If False, return the result.

    Returns:
        CompletedProcess if exit_on_complete=False, otherwise exits.
    """
    config_path = Path.cwd() / "config.yaml"

    try:
        env_config = get_env_config(environment, config_path)
    except Exception as e:
        click.echo(f"Error loading config: {e}", err=True)
        if exit_on_complete:
            sys.exit(1)
        return None

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

    if exit_on_complete:
        sys.exit(result.returncode)

    return result


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
@click.option("--table", "-t", "object_type", flag_value="table", help="Create table SQL file")
@click.option("--view", "-v", "object_type", flag_value="view", help="Create view SQL file")
@click.option(
    "--dict", "-d", "object_type", flag_value="dictionary", help="Create dictionary SQL file"
)
def new(environment: str, name: str, object_type: str | None) -> None:
    """Create a new migration.

    Creates a new migration file with the given name. Edit the generated file
    to add your upgrade() and downgrade() logic.

    Use --table, --view, or --dict to also create a SQL history file.
    """
    result = _run_alembic(environment, ["revision", "-m", name], exit_on_complete=False)

    if result is None or result.returncode != 0:
        sys.exit(1 if result is None else result.returncode)

    # If object_type specified, create SQL file
    if object_type:
        revision = _extract_revision_from_output(result.stdout)
        if revision:
            sql_path = _create_sql_file(name, object_type, revision)
            if sql_path:
                click.echo(f"  Created {sql_path.relative_to(Path.cwd())}")
        else:
            click.echo("Warning: Could not extract revision ID, SQL file not created", err=True)

    sys.exit(0)


def _extract_revision_from_output(stdout: str) -> str | None:
    """Extract revision ID from alembic output by reading the generated file."""
    # Find the generated file path from output
    # Format: "Generating /path/to/migrations/versions/<filename>.py ...  done"
    match = re.search(r"Generating (.+\.py)", stdout)
    if not match:
        return None

    migration_file = Path(match.group(1))
    if not migration_file.exists():
        return None

    # Parse revision from file content
    content = migration_file.read_text()
    rev_match = re.search(r'revision = ["\'](\w+)["\']', content)
    return rev_match.group(1) if rev_match else None


def _create_sql_file(name: str, object_type: str, revision: str) -> Path | None:
    """Create SQL history file for a migration.

    Args:
        name: Object name (e.g., "users")
        object_type: One of "table", "view", "dictionary"
        revision: Alembic revision ID

    Returns:
        Path to created file, or None if failed
    """
    # Determine directory (tables, views, dictionaries)
    type_dir = f"{object_type}s" if object_type != "dictionary" else "dictionaries"
    sql_dir = Path.cwd() / "migrations" / "sql" / "history" / type_dir / name
    sql_dir.mkdir(parents=True, exist_ok=True)

    # Use datetime prefix for ordering (matches alembic's file_template format)
    now = datetime.now()
    date_prefix = now.strftime("%Y_%m_%d_%H%M")

    # Create SQL file with minimal header
    sql_file = sql_dir / f"{date_prefix}_{revision}.sql"
    template = f"""-- {name} {object_type}
-- Migration: {revision}
-- Created: {now.strftime("%Y-%m-%d %H:%M")}

"""
    sql_file.write_text(template)
    return sql_file


@main.command()
@click.option(
    "--user",
    "target",
    flag_value="user",
    default=True,
    help="Install to ~/.claude/skills/ (default)",
)
@click.option("--project", "target", flag_value="project", help="Install to ./.claude/skills/")
def skill(target: str) -> None:
    """Install the ch-migrate Claude skill.

    Copies the skill file to help Claude assist with ch-migrate integration.

    \b
    Locations:
      --user     ~/.claude/skills/ch-migrate/  (default, for all projects)
      --project  ./.claude/skills/ch-migrate/  (current project only)
    """
    # Find the skill bundled with this package
    skill_src = Path(__file__).parent / "skills" / "ch-migrate" / "SKILL.md"

    if not skill_src.exists():
        click.echo(f"Error: Skill file not found at {skill_src}", err=True)
        sys.exit(1)

    # Determine destination
    if target == "user":
        skill_dir = Path.home() / ".claude" / "skills" / "ch-migrate"
    else:
        skill_dir = Path.cwd() / ".claude" / "skills" / "ch-migrate"

    skill_dst = skill_dir / "SKILL.md"

    # Create directory and copy
    skill_dir.mkdir(parents=True, exist_ok=True)

    if skill_dst.exists():
        click.echo(f"Skill already exists at {skill_dst}")
        if not click.confirm("Overwrite?"):
            click.echo("Aborted.")
            return

    shutil.copy(skill_src, skill_dst)
    click.echo(f"Installed skill to {skill_dst}")


if __name__ == "__main__":
    main()

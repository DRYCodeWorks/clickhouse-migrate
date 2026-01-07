"""Command-line interface for clickhouse-alembic."""

import shutil
import sys
from pathlib import Path

import click


def get_template_path(name: str) -> Path:
    """Get path to a template file."""
    return Path(__file__).parent / "templates" / "project" / f"{name}.template"


def render_template(template_path: Path, **kwargs: str) -> str:
    """Render a template with substitutions."""
    content = template_path.read_text()
    for key, value in kwargs.items():
        content = content.replace(f"{{{key}}}", value)
    return content


@click.group()
@click.version_option()
def main() -> None:
    """ClickHouse migration tool built on Alembic."""
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
    click.echo("  3. Run: ./migrate.sh dev bootstrap")
    click.echo("  4. Create your first migration: ./migrate.sh dev new create_users_table")


@main.command()
@click.argument("environment")
def bootstrap(environment: str) -> None:
    """Initialize database and users for an environment.

    Creates the database, dict_reader user, and service user.
    Requires admin credentials in .env.local.
    """
    from clickhouse_alembic.bootstrap import run_bootstrap

    try:
        run_bootstrap(environment)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

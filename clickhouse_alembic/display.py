"""Rich terminal rendering for migration history and status."""

from __future__ import annotations

from typing import Any

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from clickhouse_alembic.rebase import RevisionGraph


def _short_error(error: str) -> str:
    """Extract a concise message from verbose connection errors."""
    # clickhouse_connect wraps urllib3 errors in nested messages.
    # Pull out the innermost bracketed reason if present.
    import re

    inner = re.search(r"\[Errno \d+\] (.+?)(?:\)|\")", error)
    if inner:
        return inner.group(1)
    # Fall back to first line
    return error.split("\n")[0][:120]


def render_history(
    graph: RevisionGraph,
    applied_revisions: set[str] | None,
    db_error: str | None = None,
    console: Console | None = None,
) -> None:
    """Render migration history as a Rich tree.

    Args:
        graph: Parsed revision graph from migration files.
        applied_revisions: Set of applied revision IDs, or None if DB unreachable.
        db_error: Error message if DB connection failed.
        console: Optional Console for testability.
    """
    console = console or Console()

    if db_error:
        console.print(f"[yellow]Warning: Could not connect to database: {_short_error(db_error)}[/yellow]")
        console.print("[dim]Showing file-based history only (status unknown)[/dim]")
        console.print()

    heads = set(graph.heads())
    roots = graph.children.get(None, [])

    if not roots:
        console.print("[dim]No migrations found.[/dim]")
        return

    tree = Tree("[bold]Migration History[/bold]")

    for root_rev in roots:
        _add_branch(tree, root_rev, graph, applied_revisions, heads)

    console.print(tree)


def _add_branch(
    parent: Tree,
    revision: str,
    graph: RevisionGraph,
    applied_revisions: set[str] | None,
    heads: set[str],
    visited: set[str] | None = None,
) -> None:
    """Recursively add a revision and its children to the tree."""
    if visited is None:
        visited = set()

    if revision in visited:
        parent.add(f"[red]\u21ba {revision[:8]}  (cycle detected)[/red]")
        return
    visited.add(revision)

    migration = graph.migrations.get(revision)
    if not migration:
        return

    short_rev = revision[:8]
    desc = migration.description or ""

    if applied_revisions is None:
        marker = "[dim]\u2500[/dim]"
        label = f"{marker} [dim]{short_rev}[/dim]  {desc}"
    elif revision in applied_revisions:
        marker = "[green]\u2713[/green]"
        label = f"{marker} [green]{short_rev}[/green]  {desc}"
    else:
        marker = "[yellow]\u25cb[/yellow]"
        label = f"{marker} [yellow]{short_rev}[/yellow]  {desc}"

    if revision in heads:
        label += "  [bold cyan](HEAD)[/bold cyan]"

    node = parent.add(label)

    for child_rev in graph.children.get(revision, []):
        _add_branch(node, child_rev, graph, applied_revisions, heads, visited)


def render_status(
    env_name: str,
    env_config: dict[str, Any],
    graph: RevisionGraph,
    applied_revisions: set[str] | None,
    db_error: str | None = None,
    console: Console | None = None,
) -> None:
    """Render migration status as a Rich panel.

    Args:
        env_name: Environment name (e.g., "dev").
        env_config: Environment config dict.
        graph: Parsed revision graph.
        applied_revisions: Set of applied revision IDs, or None if DB unreachable.
        db_error: Error message if DB connection failed.
        console: Optional Console for testability.
    """
    console = console or Console()

    env_table = Table(show_header=False, box=None, padding=(0, 2))
    env_table.add_column(style="bold")
    env_table.add_column()
    env_table.add_row("Host", env_config.get("host", "unknown"))
    env_table.add_row("Database", env_config.get("database", "unknown"))
    env_table.add_row(
        "User", env_config.get("migration_user") or env_config.get("user", "unknown")
    )

    all_revisions = set(graph.migrations.keys())
    heads = graph.heads()

    status_text = Text()

    if db_error:
        status_text.append(f"\nDatabase unreachable: {_short_error(db_error)}\n", style="yellow")
        status_text.append(f"\nMigrations on disk: ", style="bold")
        status_text.append(f"{len(all_revisions)}")
        status_text.append(f"\nHeads: ", style="bold")
        status_text.append(", ".join(h[:8] for h in heads) or "none")
    else:
        applied = applied_revisions or set()
        pending = all_revisions - applied
        n_applied = len(applied)
        n_pending = len(pending)

        # Find last applied: walk from each head toward root, first hit in applied wins
        last_applied_desc = "none"
        for head in heads:
            chain = graph.walk_to_root(head)
            for rev in chain:
                if rev in applied:
                    m = graph.migrations[rev]
                    desc = m.description or ""
                    last_applied_desc = f"{rev[:8]}  {desc}"
                    break
            if last_applied_desc != "none":
                break

        if n_pending == 0:
            head_status = ("At head", "green")
        else:
            head_status = (f"Behind by {n_pending}", "yellow")

        status_text.append("\nApplied:      ", style="bold")
        status_text.append(f"{n_applied}")
        status_text.append("\nPending:      ", style="bold")
        status_text.append(f"{n_pending}")
        status_text.append("\nLast applied: ", style="bold")
        status_text.append(last_applied_desc)
        status_text.append("\nHead status:  ", style="bold")
        status_text.append(head_status[0], style=head_status[1])

    panel = Panel(
        Group(env_table, status_text),
        title=f"[bold]{env_name}[/bold] migration status",
        border_style="blue",
    )
    console.print(panel)

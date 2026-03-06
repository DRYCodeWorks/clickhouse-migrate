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


def _format_revision(
    revision: str,
    graph: RevisionGraph,
    applied_revisions: set[str] | None,
    heads: set[str],
) -> str:
    """Format a single revision line."""
    migration = graph.migrations.get(revision)
    desc = migration.description if migration else ""
    short_rev = revision[:8]

    if applied_revisions is None:
        line = f"  [dim]\u2500 {short_rev}[/dim]  {desc}"
    elif revision in applied_revisions:
        line = f"  [green]\u2713 {short_rev}[/green]  {desc}"
    else:
        line = f"  [yellow]\u25cb {short_rev}[/yellow]  {desc}"

    if revision in heads:
        line += "  [bold cyan](HEAD)[/bold cyan]"

    return line


def render_history(
    graph: RevisionGraph,
    applied_revisions: set[str] | None,
    db_error: str | None = None,
    console: Console | None = None,
) -> None:
    """Render migration history as a flat list, newest first.

    Linear chains render flat (like git log). Branches are shown as
    indented sections only where the graph actually forks.

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

    # Build ordered list from heads back to roots (newest first).
    ordered = _build_display_order(graph)

    console.print("[bold]Migration History[/bold]")
    console.print()

    visited: set[str] = set()
    for revision in ordered:
        if revision in visited:
            continue
        visited.add(revision)
        console.print(_format_revision(revision, graph, applied_revisions, heads))

    console.print()


def _build_display_order(graph: RevisionGraph) -> list[str]:
    """Build a newest-first display order by walking from heads to roots.

    For a linear chain this produces a simple reverse-chronological list.
    For branches, interleaves them by walking each head fully before the next.
    Falls back to all revisions if no heads are found (e.g., due to a cycle).
    """
    heads = graph.heads()
    visited: set[str] = set()
    ordered: list[str] = []

    for head in heads:
        chain = graph.walk_to_root(head)
        for rev in chain:
            if rev not in visited:
                visited.add(rev)
                ordered.append(rev)

    # Fallback: include any revisions not reachable from heads (e.g., cycles).
    for rev in graph.migrations:
        if rev not in visited:
            ordered.append(rev)

    return ordered


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


def render_lint_report(
    report: Any,
    *,
    runtime: bool = False,
    console: Console | None = None,
) -> None:
    """Render lint results as a Rich table.

    Args:
        report: LintReport with results.
        runtime: Whether runtime rules were included.
        console: Optional Console for testability.
    """
    console = console or Console()

    if not report.results:
        mode = "static + runtime" if runtime else "static"
        console.print(f"[green]No lint issues found ({mode} analysis).[/green]")
        return

    table = Table(title="Lint Results", show_lines=False)
    table.add_column("Severity", width=8)
    table.add_column("Rule", width=22)
    table.add_column("File", width=30)
    table.add_column("Line", width=5, justify="right")
    table.add_column("Message")

    for r in report.results:
        if r.severity.value == "error":
            sev_style = "bold red"
            sev_text = "ERROR"
        else:
            sev_style = "yellow"
            sev_text = "WARN"

        table.add_row(
            Text(sev_text, style=sev_style),
            r.rule,
            r.file or "",
            str(r.line) if r.line else "",
            r.message,
        )

    console.print(table)
    console.print()

    summary_parts = []
    if report.error_count:
        summary_parts.append(f"[bold red]{report.error_count} error(s)[/bold red]")
    if report.warning_count:
        summary_parts.append(f"[yellow]{report.warning_count} warning(s)[/yellow]")

    console.print(f"  {', '.join(summary_parts)}")


def render_snapshot_progress(
    output_dir: str,
    counts: dict[str, int],
    excluded: int = 0,
    console: Console | None = None,
) -> None:
    """Render snapshot completion summary.

    Args:
        output_dir: Path to the snapshot directory.
        counts: Dict mapping object type to count (e.g. {"tables": 3, "views": 1}).
        excluded: Number of objects excluded by filter.
        console: Optional Console for testability.
    """
    console = console or Console()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold")
    table.add_column(justify="right")

    total = 0
    for obj_type, count in counts.items():
        if count > 0:
            table.add_row(obj_type.replace("_", " ").title(), str(count))
            total += count

    status_text = Text()
    status_text.append(f"\nSnapshot saved to ", style="dim")
    status_text.append(output_dir, style="bold")
    status_text.append(f"\n{total} objects captured", style="green")
    if excluded:
        status_text.append(f", {excluded} excluded", style="dim")

    panel = Panel(
        Group(table, status_text),
        title="[bold]Schema Snapshot[/bold]",
        border_style="blue",
    )
    console.print(panel)


def render_diff_report(
    diffs: list[Any],
    *,
    console: Console | None = None,
) -> None:
    """Render schema diff results as a Rich table.

    Args:
        diffs: List of SchemaDiff objects from compare_schemas().
        console: Optional Console for testability.
    """
    from clickhouse_alembic.diff import DiffStatus

    console = console or Console()

    in_sync = [d for d in diffs if d.status == DiffStatus.IN_SYNC]
    modified = [d for d in diffs if d.status == DiffStatus.MODIFIED]
    local_only = [d for d in diffs if d.status == DiffStatus.LOCAL_ONLY]
    remote_only = [d for d in diffs if d.status == DiffStatus.REMOTE_ONLY]

    has_drift = bool(modified or local_only or remote_only)

    if not has_drift:
        console.print(f"[green]All {len(in_sync)} objects in sync.[/green]")
        return

    table = Table(title="Schema Diff", show_lines=False)
    table.add_column("Status", width=12)
    table.add_column("Type", width=20)
    table.add_column("Name", width=30)
    table.add_column("Details")

    for d in local_only:
        table.add_row(
            Text("LOCAL ONLY", style="yellow"),
            d.obj_type,
            d.name,
            "Exists in snapshot but not in DB",
        )

    for d in remote_only:
        table.add_row(
            Text("REMOTE ONLY", style="cyan"),
            d.obj_type,
            d.name,
            "Exists in DB but not in snapshot",
        )

    for d in modified:
        details = "; ".join(fd.message for fd in d.field_diffs)
        table.add_row(
            Text("MODIFIED", style="bold red"),
            d.obj_type,
            d.name,
            details,
        )

    console.print(table)
    console.print()

    parts = []
    if modified:
        parts.append(f"[bold red]{len(modified)} modified[/bold red]")
    if local_only:
        parts.append(f"[yellow]{len(local_only)} local only[/yellow]")
    if remote_only:
        parts.append(f"[cyan]{len(remote_only)} remote only[/cyan]")
    if in_sync:
        parts.append(f"[green]{len(in_sync)} in sync[/green]")

    console.print(f"  {', '.join(parts)}")


_OBJ_TYPE_STYLES = {
    "table": ("bold", "T"),
    "view": ("cyan", "V"),
    "materialized_view": ("magenta", "MV"),
    "dictionary": ("yellow", "D"),
}

_DEP_TYPE_LABELS = {
    "schema": "[dim]schema[/dim]",
    "data_flow": "[bold blue]data_flow[/bold blue]",
}


def render_dependency_tree(
    graph: Any,
    *,
    console: Console | None = None,
) -> None:
    """Render a dependency graph as a Rich Tree.

    Each root node (no incoming edges) gets a tree branch. Dependent objects
    are shown as children with edge type annotations.

    Args:
        graph: A DependencyGraph from introspect.
        console: Optional Console for testability.
    """
    console = console or Console()

    if not graph.nodes:
        console.print("[dim]No objects found in database.[/dim]")
        return

    tree = Tree("[bold]Dependency Graph[/bold]")

    # Build adjacency: source -> [(target, dep_label)]
    # Deduplicate: if multiple edge types exist for the same pair, combine them
    children_raw: dict[str, dict[str, list[str]]] = {name: {} for name in graph.nodes}
    has_parent: set[str] = set()
    for edge in graph.edges:
        if edge.source in children_raw and edge.target in graph.nodes:
            children_raw[edge.source].setdefault(edge.target, []).append(edge.dep_type.value)
            has_parent.add(edge.target)

    children_map: dict[str, list[tuple[str, str]]] = {}
    for source, targets in children_raw.items():
        children_map[source] = [
            (target, " + ".join(dep_types)) for target, dep_types in targets.items()
        ]

    # Roots: nodes with no incoming edges
    roots = [name for name in graph.nodes if name not in has_parent]
    if not roots:
        # All nodes have parents (cycles) — just show all
        roots = sorted(graph.nodes.keys())

    def _add_node(parent_tree: Tree, name: str, dep_label: str | None, visited: set[str]) -> None:
        node = graph.nodes[name]
        style, prefix = _OBJ_TYPE_STYLES.get(node.obj_type, ("", "?"))
        label = f"[{style}][{prefix}][/{style}] {name}"
        if dep_label:
            label += f"  {dep_label}"

        if name in visited:
            parent_tree.add(f"{label} [dim](circular)[/dim]")
            return

        branch = parent_tree.add(label)
        visited.add(name)

        for child_name, child_dep_type in children_map.get(name, []):
            dep_str = _DEP_TYPE_LABELS.get(child_dep_type, child_dep_type)
            _add_node(branch, child_name, dep_str, visited)

    for root_name in sorted(roots):
        _add_node(tree, root_name, None, set())

    console.print(tree)
    console.print()

    # Summary
    type_counts: dict[str, int] = {}
    for node in graph.nodes.values():
        type_counts[node.obj_type] = type_counts.get(node.obj_type, 0) + 1

    parts = []
    for obj_type, count in sorted(type_counts.items()):
        _, prefix = _OBJ_TYPE_STYLES.get(obj_type, ("", "?"))
        parts.append(f"{count} {obj_type.replace('_', ' ')}s [{prefix}]")

    console.print(f"  {', '.join(parts)} — {len(graph.edges)} edges")

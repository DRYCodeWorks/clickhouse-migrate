"""Rebase dangling migration branches onto a new parent revision."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Migration:
    """A parsed Alembic migration file."""

    path: Path
    revision: str
    down_revision: str | None
    description: str | None = None
    create_date: str | None = None


@dataclass
class RevisionGraph:
    """Graph of migration revisions built from file parsing."""

    migrations: dict[str, Migration] = field(default_factory=dict)
    children: dict[str | None, list[str]] = field(default_factory=lambda: {None: []})

    def heads(self) -> list[str]:
        """Find revisions that have no children (tips of branches)."""
        has_children = {parent for parent, kids in self.children.items() if kids}
        return [rev for rev in self.migrations if rev not in has_children]

    def ancestors(self, revision: str) -> set[str]:
        """Return all ancestors of a revision (not including itself).

        Stops if a cycle is detected to prevent infinite loops.
        """
        result: set[str] = set()
        current = self.migrations.get(revision)
        while current and current.down_revision:
            if current.down_revision in result:
                break
            result.add(current.down_revision)
            current = self.migrations.get(current.down_revision)
        return result

    def walk_to_root(self, revision: str) -> list[str]:
        """Walk from revision back to root, returning the chain.

        Stops if a cycle is detected to prevent infinite loops.
        """
        chain = [revision]
        visited = {revision}
        current = self.migrations.get(revision)
        while current and current.down_revision:
            if current.down_revision in visited:
                break
            visited.add(current.down_revision)
            chain.append(current.down_revision)
            current = self.migrations.get(current.down_revision)
        return chain


def parse_migration(path: Path) -> Migration | None:
    """Extract revision and down_revision from a migration file.

    Returns None if the file can't be parsed.
    """
    content = path.read_text()

    rev_match = re.search(r"^revision\s*=\s*['\"](\w+)['\"]", content, re.MULTILINE)
    down_match = re.search(
        r"^down_revision\s*=\s*['\"](\w+)['\"]", content, re.MULTILINE
    )

    if not rev_match:
        return None

    # Extract description from first line of module docstring
    description = None
    desc_match = re.search(r'^"""(.+?)$', content, re.MULTILINE)
    if desc_match:
        description = desc_match.group(1).strip()

    # Extract create date
    create_date = None
    date_match = re.search(r"^Create Date:\s*(.+)$", content, re.MULTILINE)
    if date_match:
        create_date = date_match.group(1).strip()

    return Migration(
        path=path,
        revision=rev_match.group(1),
        down_revision=down_match.group(1) if down_match else None,
        description=description,
        create_date=create_date,
    )


def build_revision_graph(versions_dir: Path) -> RevisionGraph:
    """Scan migration files and build a revision graph."""
    graph = RevisionGraph()

    for path in sorted(versions_dir.glob("*.py")):
        migration = parse_migration(path)
        if migration:
            graph.migrations[migration.revision] = migration
            if migration.down_revision not in graph.children:
                graph.children[migration.down_revision] = []
            graph.children[migration.down_revision].append(migration.revision)

    return graph


def find_branch_roots(
    graph: RevisionGraph, onto: str
) -> list[Migration]:
    """Find the root migration of each dangling branch.

    For each head that isn't `onto` (or a descendant of `onto`),
    walk back to find the first migration whose down_revision is
    an ancestor of `onto` (or is `onto` itself). That migration's
    down_revision is what gets rewritten.

    Returns the list of migrations that need their down_revision changed.
    """
    heads = graph.heads()
    onto_ancestors = graph.ancestors(onto) | {onto}
    roots = []

    for head in heads:
        if head == onto:
            continue

        # Walk back from this head
        chain = graph.walk_to_root(head)
        for rev_id in chain:
            migration = graph.migrations[rev_id]
            if migration.down_revision in onto_ancestors:
                roots.append(migration)
                break

    return roots


def rewrite_down_revision(path: Path, old_rev: str, new_rev: str) -> str:
    """Rewrite down_revision in a migration file.

    Updates both:
    - The `down_revision = '...'` variable assignment
    - The `Revises: ...` line in the docstring

    Returns the new file content (does not write to disk).
    """
    content = path.read_text()

    # Replace the variable assignment
    content = re.sub(
        r"(^down_revision\s*=\s*['\"])" + re.escape(old_rev) + r"(['\"])",
        r"\g<1>" + new_rev + r"\2",
        content,
        count=1,
        flags=re.MULTILINE,
    )

    # Replace the Revises: line in the docstring
    content = re.sub(
        r"(^Revises:\s*)" + re.escape(old_rev),
        r"\g<1>" + new_rev,
        content,
        count=1,
        flags=re.MULTILINE,
    )

    return content


@dataclass
class RebaseChange:
    """A planned change to a migration file."""

    migration: Migration
    old_down_revision: str
    new_down_revision: str


def plan_rebase(versions_dir: Path, onto: str) -> list[RebaseChange]:
    """Plan the rebase without making changes.

    Returns a list of changes that would be made.
    Raises ValueError if onto revision is not found or nothing to do.
    """
    graph = build_revision_graph(versions_dir)

    if onto not in graph.migrations:
        raise ValueError(f"Revision '{onto}' not found in migrations")

    heads = graph.heads()
    if len(heads) <= 1:
        raise ValueError("Only one head found — nothing to rebase")

    roots = find_branch_roots(graph, onto)
    if not roots:
        raise ValueError("No dangling branches found to rebase")

    return [
        RebaseChange(
            migration=root,
            old_down_revision=root.down_revision,
            new_down_revision=onto,
        )
        for root in roots
        if root.down_revision != onto
    ]


def apply_rebase(changes: list[RebaseChange]) -> None:
    """Apply planned rebase changes to disk."""
    for change in changes:
        new_content = rewrite_down_revision(
            change.migration.path,
            change.old_down_revision,
            change.new_down_revision,
        )
        change.migration.path.write_text(new_content)

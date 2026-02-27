"""Tests for migration rebase functionality."""

from pathlib import Path
from textwrap import dedent

import pytest

from clickhouse_alembic.rebase import (
    apply_rebase,
    build_revision_graph,
    find_branch_roots,
    parse_migration,
    plan_rebase,
    rewrite_down_revision,
)


def _write_migration(versions_dir: Path, revision: str, down_revision: str | None, name: str = "migration") -> Path:
    """Write a minimal migration file and return its path."""
    down_rev_str = f"'{down_revision}'" if down_revision else "None"
    revises_str = down_revision if down_revision else ""
    content = dedent(f"""\
        \"""{name}

        Revision ID: {revision}
        Revises: {revises_str}
        Create Date: 2026-01-01 00:00
        \"""

        from alembic import op

        revision = '{revision}'
        down_revision = {down_rev_str}
        branch_labels = None
        depends_on = None


        def upgrade() -> None:
            pass


        def downgrade() -> None:
            pass
    """)
    path = versions_dir / f"2026_01_01_0000_{revision}_{name}.py"
    path.write_text(content)
    return path


class TestParseMigration:
    def test_parses_revision_and_down_revision(self, tmp_path):
        path = _write_migration(tmp_path, "abc123", "def456")
        result = parse_migration(path)
        assert result is not None
        assert result.revision == "abc123"
        assert result.down_revision == "def456"

    def test_parses_root_migration(self, tmp_path):
        path = _write_migration(tmp_path, "abc123", None)
        result = parse_migration(path)
        assert result is not None
        assert result.revision == "abc123"
        assert result.down_revision is None

    def test_returns_none_for_unparseable_file(self, tmp_path):
        path = tmp_path / "bad.py"
        path.write_text("# no revision here\n")
        assert parse_migration(path) is None


class TestBuildRevisionGraph:
    def test_builds_linear_chain(self, tmp_path):
        _write_migration(tmp_path, "aaa", None, "first")
        _write_migration(tmp_path, "bbb", "aaa", "second")
        _write_migration(tmp_path, "ccc", "bbb", "third")

        graph = build_revision_graph(tmp_path)
        assert len(graph.migrations) == 3
        assert graph.heads() == ["ccc"]

    def test_builds_forked_graph(self, tmp_path):
        _write_migration(tmp_path, "base", None, "base")
        _write_migration(tmp_path, "f1a", "base", "feature1a")
        _write_migration(tmp_path, "f1b", "f1a", "feature1b")
        _write_migration(tmp_path, "f2a", "base", "feature2a")
        _write_migration(tmp_path, "f2b", "f2a", "feature2b")

        graph = build_revision_graph(tmp_path)
        assert len(graph.migrations) == 5
        heads = sorted(graph.heads())
        assert heads == ["f1b", "f2b"]


class TestRevisionGraphHeads:
    def test_single_head(self, tmp_path):
        _write_migration(tmp_path, "aaa", None)
        _write_migration(tmp_path, "bbb", "aaa")

        graph = build_revision_graph(tmp_path)
        assert graph.heads() == ["bbb"]

    def test_multiple_heads(self, tmp_path):
        _write_migration(tmp_path, "base", None, "base")
        _write_migration(tmp_path, "br1", "base", "branch1")
        _write_migration(tmp_path, "br2", "base", "branch2")

        graph = build_revision_graph(tmp_path)
        assert sorted(graph.heads()) == ["br1", "br2"]


class TestRevisionGraphAncestors:
    def test_ancestors_of_head(self, tmp_path):
        _write_migration(tmp_path, "aaa", None, "first")
        _write_migration(tmp_path, "bbb", "aaa", "second")
        _write_migration(tmp_path, "ccc", "bbb", "third")

        graph = build_revision_graph(tmp_path)
        assert graph.ancestors("ccc") == {"aaa", "bbb"}

    def test_ancestors_of_root(self, tmp_path):
        _write_migration(tmp_path, "aaa", None)

        graph = build_revision_graph(tmp_path)
        assert graph.ancestors("aaa") == set()


class TestFindBranchRoots:
    def test_finds_root_of_dangling_branch(self, tmp_path):
        _write_migration(tmp_path, "base", None, "base")
        _write_migration(tmp_path, "f1a", "base", "feature1a")
        _write_migration(tmp_path, "f1b", "f1a", "feature1b")
        _write_migration(tmp_path, "f2a", "base", "feature2a")
        _write_migration(tmp_path, "f2b", "f2a", "feature2b")

        graph = build_revision_graph(tmp_path)
        roots = find_branch_roots(graph, "f1b")

        assert len(roots) == 1
        assert roots[0].revision == "f2a"
        assert roots[0].down_revision == "base"

    def test_finds_multiple_dangling_branches(self, tmp_path):
        _write_migration(tmp_path, "base", None, "base")
        _write_migration(tmp_path, "f1a", "base", "feature1a")
        _write_migration(tmp_path, "f2a", "base", "feature2a")
        _write_migration(tmp_path, "f3a", "base", "feature3a")

        graph = build_revision_graph(tmp_path)
        roots = find_branch_roots(graph, "f1a")

        assert len(roots) == 2
        root_revs = sorted(r.revision for r in roots)
        assert root_revs == ["f2a", "f3a"]

    def test_no_roots_when_single_head(self, tmp_path):
        _write_migration(tmp_path, "aaa", None)
        _write_migration(tmp_path, "bbb", "aaa")

        graph = build_revision_graph(tmp_path)
        roots = find_branch_roots(graph, "bbb")
        assert roots == []


class TestRewriteDownRevision:
    def test_rewrites_variable_and_docstring(self, tmp_path):
        path = _write_migration(tmp_path, "f2a", "base")
        new_content = rewrite_down_revision(path, "base", "f1b")

        assert "down_revision = 'f1b'" in new_content
        assert "Revises: f1b" in new_content
        assert "base" not in new_content

    def test_preserves_revision_id(self, tmp_path):
        path = _write_migration(tmp_path, "f2a", "base")
        new_content = rewrite_down_revision(path, "base", "f1b")

        assert "revision = 'f2a'" in new_content


class TestPlanRebase:
    def test_plans_rebase_correctly(self, tmp_path):
        _write_migration(tmp_path, "base", None, "base")
        _write_migration(tmp_path, "f1a", "base", "feature1a")
        _write_migration(tmp_path, "f1b", "f1a", "feature1b")
        _write_migration(tmp_path, "f2a", "base", "feature2a")
        _write_migration(tmp_path, "f2b", "f2a", "feature2b")

        changes = plan_rebase(tmp_path, "f1b")

        assert len(changes) == 1
        assert changes[0].migration.revision == "f2a"
        assert changes[0].old_down_revision == "base"
        assert changes[0].new_down_revision == "f1b"

    def test_raises_for_unknown_revision(self, tmp_path):
        _write_migration(tmp_path, "aaa", None)

        with pytest.raises(ValueError, match="not found"):
            plan_rebase(tmp_path, "nonexistent")

    def test_raises_for_single_head(self, tmp_path):
        _write_migration(tmp_path, "aaa", None)
        _write_migration(tmp_path, "bbb", "aaa")

        with pytest.raises(ValueError, match="Only one head"):
            plan_rebase(tmp_path, "bbb")

    def test_onto_does_not_need_to_be_a_head(self, tmp_path):
        """onto can be a non-head revision (e.g., deployed rev with existing branches)."""
        _write_migration(tmp_path, "base", None, "base")
        _write_migration(tmp_path, "f1a", "base", "feature1a")
        _write_migration(tmp_path, "f1b", "f1a", "feature1b")
        _write_migration(tmp_path, "f2a", "f1b", "feature2a")
        _write_migration(tmp_path, "f3a", "base", "feature3a")

        # f1b is not a head (f2a branches off it), but rebase should still work
        changes = plan_rebase(tmp_path, "f1b")
        assert len(changes) == 1
        assert changes[0].migration.revision == "f3a"

    def test_skips_branches_already_on_target(self, tmp_path):
        _write_migration(tmp_path, "base", None, "base")
        _write_migration(tmp_path, "f1a", "base", "feature1a")
        _write_migration(tmp_path, "f1b", "f1a", "feature1b")
        # f2a already branches off f1b
        _write_migration(tmp_path, "f2a", "f1b", "feature2a")
        # f3a still branches off base
        _write_migration(tmp_path, "f3a", "base", "feature3a")

        changes = plan_rebase(tmp_path, "f1b")

        assert len(changes) == 1
        assert changes[0].migration.revision == "f3a"


class TestApplyRebase:
    def test_end_to_end_rebase(self, tmp_path):
        """Full integration test: create forked migrations, rebase, verify files."""
        _write_migration(tmp_path, "base", None, "base")
        _write_migration(tmp_path, "f1a", "base", "feature1a")
        _write_migration(tmp_path, "f1b", "f1a", "feature1b")
        _write_migration(tmp_path, "f2a", "base", "feature2a")
        _write_migration(tmp_path, "f2b", "f2a", "feature2b")

        changes = plan_rebase(tmp_path, "f1b")
        apply_rebase(changes)

        # Verify f2a now points to f1b
        graph = build_revision_graph(tmp_path)
        assert graph.migrations["f2a"].down_revision == "f1b"

        # Verify f2b still points to f2a (unchanged)
        assert graph.migrations["f2b"].down_revision == "f2a"

        # Verify docstring was updated
        f2a_content = changes[0].migration.path.read_text()
        assert "Revises: f1b" in f2a_content

    def test_rebase_with_multiple_dangling_branches(self, tmp_path):
        _write_migration(tmp_path, "base", None, "base")
        _write_migration(tmp_path, "f1a", "base", "feature1a")
        _write_migration(tmp_path, "f1b", "f1a", "feature1b")
        _write_migration(tmp_path, "f2a", "base", "feature2a")
        _write_migration(tmp_path, "f3a", "base", "feature3a")

        changes = plan_rebase(tmp_path, "f1b")
        apply_rebase(changes)

        graph = build_revision_graph(tmp_path)
        assert graph.migrations["f2a"].down_revision == "f1b"
        assert graph.migrations["f3a"].down_revision == "f1b"

        # f1b should now have two children
        heads = sorted(graph.heads())
        assert heads == ["f2a", "f3a"]

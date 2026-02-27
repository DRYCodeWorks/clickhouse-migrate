# Migration Rebase

Repoint dangling migration branches onto the current deployed head, turning forked migration histories into clean branch points off the latest deployed revision.

## Problem

When two features branch off the same base migration and feature 1 lands first, feature 2's migrations still reference the old base as their parent. This creates unnecessary forks in the migration graph. We want a command that moves dangling branches forward to branch off the deployed head.

## Command Interface

### Guided (default)

```bash
ch-migrate rebase <env>
```

1. Runs `alembic heads` to find all head revisions
2. Runs `alembic current` against the env's database to identify the deployed head
3. Shows dangling branches (heads that aren't deployed) with migration names and dates
4. Rewrites each dangling branch's root migration to point at the deployed head
5. Asks for confirmation before writing

### Explicit

```bash
ch-migrate rebase <env> --onto <revision>
```

Skips auto-detection. Uses the provided revision as the new parent for all dangling branches. Useful when you don't have database access or are scripting.

### Dry run

```bash
ch-migrate rebase <env> --dry-run
```

Prints planned changes and exits without prompting or writing.

## Algorithm

1. **Find heads**: Parse output of `alembic heads`
2. **Find deployed head**: Parse output of `alembic current` for the given env. If no database connection, require `--onto`.
3. **Find branch roots**: For each non-deployed head, walk back through `down_revision` links until finding a revision that is an ancestor of the deployed head. The migration whose `down_revision` is that shared ancestor is the branch root.
4. **Rewrite**: In each branch root migration file, replace the old `down_revision` hash with the deployed head's hash in:
   - The `down_revision = '...'` variable assignment
   - The `Revises:` line in the module docstring
5. **Confirm**: Display a diff-style summary of changes. Write files only after user confirmation (unless `--dry-run`).

### Example

Before:
```
base ── f1a ── f1b  (deployed head)
  ├─── f2a ── f2b  (dangling)
  └─── f3a ── f3b  (dangling)
```

After:
```
base ── f1a ── f1b ── f2a ── f2b
                └─── f3a ── f3b
```

Only `f2a` and `f3a` have their `down_revision` rewritten (from `base` to `f1b`). The rest of each chain is untouched.

## Implementation

### File manipulation

Parse migration files directly rather than using Alembic's Python API (consistent with how the CLI already wraps Alembic via subprocess). Replace the old parent hash with the new one in the metadata block above `upgrade()` to avoid accidental replacements in SQL logic.

### Safety checks

- **Single head**: Nothing to rebase. Exit with a message.
- **No heads**: Error — project has no migrations.
- **Dirty working tree**: Abort if migration files have uncommitted changes (like `git rebase` refusing on a dirty worktree).
- **No database connection**: Fall back to requiring `--onto`.

## Out of Scope

- **Database updates**: Does not touch `alembic_version` tables.
- **Revision ID regeneration**: Migrations keep their own hashes; only the parent pointer changes.
- **Branch ordering**: Multiple dangling branches are independently repointed; they remain parallel.
- **Merge migrations**: Use Alembic's `alembic merge` for that.

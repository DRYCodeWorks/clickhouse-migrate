# clickhouse-alembic

Alembic-based migrations for ClickHouse, optimized for ClickHouse Cloud.

## Features

- **Multi-environment support** - Manage dev, staging, and production with separate configs
- **ClickHouse Cloud optimized** - Uses `SharedReplacingMergeTree`, handles non-transactional DDL
- **Object-centric SQL history** - Track all versions of each table/view/dictionary
- **Zero-downtime migrations** - `EXCHANGE TABLES` pattern for safe schema changes
- **Bootstrap command** - One-command database and user setup
- **YAML + env vars** - Config in version control, secrets in environment

## Quick Start

### Installation

```bash
pip install clickhouse-alembic
```

### Initialize a Project

```bash
# Create a new project
mkdir my-clickhouse-project
cd my-clickhouse-project

# Initialize with ch-migrate
ch-migrate init

# Or initialize in current directory with custom name
ch-migrate init --name my_project
```

This creates:
```
my-clickhouse-project/
├── config.yaml              # ClickHouse hosts and settings
├── .env.local.example       # Template for secrets
├── .gitignore
├── alembic.ini
├── migrate.sh               # Migration helper script
└── migrations/
    ├── env.py
    ├── script.py.mako
    ├── versions/            # Migration files go here
    └── sql/
        ├── bootstrap/
        └── history/
            ├── tables/
            ├── views/
            └── dictionaries/
```

### Configure

1. Edit `config.yaml` with your ClickHouse hosts:

```yaml
project:
  name: my_project

defaults:
  port: 8443
  secure: true
  admin_user: default
  dict_reader_name: dict_reader

environments:
  dev:
    host: my-dev-instance.clickhouse.cloud
    database: my_project_dev
    user: service_dev

  production:
    host: my-prod-instance.clickhouse.cloud
    database: my_project
    user: service_prod
```

2. Copy `.env.local.example` to `.env.local` and add passwords:

```bash
CH_DEV_PASSWORD=your-dev-password
CH_DEV_ADMIN_PASSWORD=your-dev-admin-password
CH_DEV_DICT_READER_PASSWORD=your-dev-dict-password

CH_PRODUCTION_PASSWORD=your-prod-password
CH_PRODUCTION_ADMIN_PASSWORD=your-prod-admin-password
CH_PRODUCTION_DICT_READER_PASSWORD=your-prod-dict-password
```

### Bootstrap Database

```bash
# Creates database, dict_reader user, and service user
./migrate.sh dev bootstrap
```

### Create and Run Migrations

```bash
# Create a new migration
./migrate.sh dev new create_users_table

# Run pending migrations
./migrate.sh dev up

# Check status
./migrate.sh dev status

# Rollback last migration
./migrate.sh dev down
```

## Migration Patterns

### Basic Table Creation

1. Create SQL file in `migrations/sql/history/tables/users/001_<revision>.sql`:

```sql
CREATE TABLE {db}.users (
    id UInt64,
    email String,
    name String,
    created_at DateTime DEFAULT now()
)
ENGINE = SharedMergeTree
ORDER BY id
```

2. Reference in migration:

```python
from alembic import op
from clickhouse_alembic import get_db, read_sql

def upgrade():
    db = get_db()
    op.execute(read_sql("history/tables/users/001_abc123.sql", db=db))

def downgrade():
    db = get_db()
    op.execute(f"DROP TABLE IF EXISTS {db}.users")
```

### Zero-Downtime Schema Changes

Use `EXCHANGE TABLES` for data-preserving migrations:

```python
def upgrade():
    db = get_db()

    # 1. Create new table with updated schema
    op.execute(read_sql("history/tables/users/002_def456.sql", db=db)
               .replace(f"{db}.users", f"{db}.users_new"))

    # 2. Migrate data with transformations
    op.execute(f"""
        INSERT INTO {db}.users_new
        SELECT id, email, name, created_at, '' as phone
        FROM {db}.users
    """)

    # 3. Atomic swap
    op.execute(f"EXCHANGE TABLES {db}.users AND {db}.users_new")

    # 4. Drop old table
    op.execute(f"DROP TABLE {db}.users_new")
```

### Materialized View Query Updates

Use `MODIFY QUERY` to update MV logic without losing data:

```python
def upgrade():
    db = get_db()
    query = read_sql("history/views/stats_mv/queries/002_xyz789.sql", db=db)
    op.execute(f"ALTER TABLE {db}.stats_mv MODIFY QUERY {query}")
```

### Dictionary with Auto-Grant

```python
from clickhouse_alembic import create_dictionary

def upgrade():
    # Automatically grants SELECT to dict_reader on source table
    create_dictionary("history/dictionaries/dict_users/001_abc123.sql")
```

## CLI Reference

```bash
# Initialize new project
ch-migrate init [PATH] [--name NAME]

# Bootstrap database (create DB, users)
ch-migrate bootstrap <environment>

# Via migrate.sh wrapper:
./migrate.sh <env> status      # Show migration status
./migrate.sh <env> up          # Apply pending migrations
./migrate.sh <env> down        # Rollback last migration
./migrate.sh <env> new <name>  # Create new migration
./migrate.sh <env> history     # Show full history
./migrate.sh <env> bootstrap   # Initialize database
```

## Configuration Reference

### config.yaml

```yaml
project:
  name: my_project          # Project identifier

defaults:                   # Inherited by all environments
  port: 8443
  secure: true
  admin_user: default
  dict_reader_name: dict_reader

environments:
  dev:
    host: dev.clickhouse.cloud
    database: my_project_dev
    user: service_dev
    # port: 8443            # Override default
    # secure: true          # Override default
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `CH_<ENV>_PASSWORD` | Yes | Service user password |
| `CH_<ENV>_ADMIN_PASSWORD` | For bootstrap | Admin password for creating users |
| `CH_<ENV>_DICT_READER_PASSWORD` | For dictionaries | dict_reader user password |

## ClickHouse Cloud Notes

- Uses `SharedReplacingMergeTree` / `SharedMergeTree` engines
- Native port 9440 maps to HTTP port 8443
- No transactional DDL - migrations can't be atomically rolled back
- Each `op.execute()` runs one statement (no multi-statement batches)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Author

Dan Young

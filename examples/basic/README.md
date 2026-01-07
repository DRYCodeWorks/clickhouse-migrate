# Basic Example

A minimal example showing clickhouse-alembic in action.

## Setup

1. Install the package:
   ```bash
   pip install clickhouse-alembic
   ```

2. Initialize (already done in this example):
   ```bash
   ch-migrate init
   ```

3. Configure `config.yaml` with your ClickHouse host

4. Create `.env.local` with your passwords:
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with real passwords
   ```

5. Bootstrap:
   ```bash
   ./migrate.sh dev bootstrap
   ```

6. Run migrations:
   ```bash
   ./migrate.sh dev up
   ```

## Files

- `config.yaml` - ClickHouse connection settings (edit hosts)
- `.env.local.example` - Template for secrets
- `migrations/sql/history/tables/users/001_example.sql` - Example table schema

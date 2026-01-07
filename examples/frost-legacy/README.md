# ClickHouse Migration Tool

A powerful, configurable migration system for ClickHouse databases built on Alembic. This tool provides schema versioning, environment management, and advanced ClickHouse-specific features.

**Author:** Dan Young  
**License:** MIT License  
**Repository:** https://github.com/danyoung/clickhouse-migration-tool

## Features

- **Multi-environment support** - Manage local, development, staging, and production environments
- **Configurable credential systems** - Support for environment variables, AWS Secrets Manager, AWS SSM, and more
- **ClickHouse optimized** - Built-in templates for tables, materialized views, and dictionaries
- **Migration generators** - Command-line tools to generate common ClickHouse migration patterns
- **Flexible schema organization** - Modular schema system that scales with your project

## Quick Start

### 1. Installation

```bash
# Clone or download this tool
cd clickhouse-migration-tool

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies  
pip install -r requirements.txt
```

### 2. Initialize a New Project

```bash
# Initialize with simple local configuration
python config/setup.py init --template simple-local --name my-project

# Or initialize with AWS cloud configuration
python config/setup.py init --template aws-cloud --name my-project
```

This creates:
- `config/config.yaml` - Main configuration file
- `alembic.ini` - Generated Alembic configuration
- `schemas/schema.py` - Base schema definitions
- `clickhouse_migrations/` - Migration files directory

### 3. Configure Your Environment

Edit `config/config.yaml` to match your setup:

```yaml
environments:
  local:
    host: "localhost"
    port: 8123
    protocol: "http"
    database: "my_database"
```

Set environment variables for credentials:
```bash
export LOCAL_HOST=localhost
export LOCAL_PORT=8123
export LOCAL_DATABASE=my_database
export LOCAL_USERNAME=default
export LOCAL_PASSWORD=""
```

### 4. Create Your First Migration

```bash
# Generate a table migration
python generate.py table users --message "create_users_table"

# Or use standard alembic commands
alembic -n local revision -m "create_users_table"
```

### 5. Run Migrations

```bash
# Apply all pending migrations
alembic -n local upgrade head

# Check migration status
alembic -n local current
alembic -n local history
```

## Configuration

### Basic Configuration (config.yaml)

```yaml
project:
  name: "my-clickhouse-project"
  description: "ClickHouse database migrations"

credentials:
  type: "env_vars"  # or aws_secrets, aws_ssm
  
environments:
  local:
    host: "localhost"
    port: 8123
    database: "default"
  
  prod:
    host: "prod.clickhouse.example.com"
    port: 8443
    protocol: "https"
    database: "production"
```

### Credential Management

#### Environment Variables (Default)
```bash
export LOCAL_HOST=localhost
export LOCAL_PORT=8123
export LOCAL_USERNAME=default
export LOCAL_PASSWORD=mypassword
```

#### AWS Secrets Manager
```yaml
credentials:
  type: "aws_secrets"
  aws_secrets:
    region: "us-east-1"
    secret_mappings:
      prod: "prod/clickhouse/credentials"
```

#### AWS SSM Parameter Store
```yaml
credentials:
  type: "aws_ssm" 
  aws_ssm:
    region: "us-east-1"
    parameter_mappings:
      prod: "/prod/clickhouse"
```

## Migration Generators

Use the built-in generators for common ClickHouse patterns:

### Create Tables
```bash
python generate.py table events
python generate.py table user_analytics --message "analytics table"
```

### Create Materialized Views
```bash
python generate.py view daily_stats
python generate.py view user_summary --message "user aggregation view"
```

### Create Dictionaries
```bash
python generate.py dictionary users
python generate.py dictionary categories --message "category lookup"
```

### List Available Templates
```bash
python generate.py list-templates
```

## Migration Commands

### Environment Management
```bash
# Work with different environments
alembic -n local upgrade head      # Local development
alembic -n dev upgrade head        # Development environment  
alembic -n prod upgrade head       # Production environment

# Check current migration status
alembic -n local current
alembic -n local history --verbose
```

### Creating Migrations
```bash
# Auto-generate from schema changes
alembic -n local revision --autogenerate -m "add user table"

# Create empty migration
alembic -n local revision -m "custom changes"

# Generate from templates
python generate.py table my_table
python generate.py view my_view
```

### Migration Operations
```bash
# Apply all pending migrations
alembic -n local upgrade head

# Apply specific number of migrations
alembic -n local upgrade +2

# Rollback migrations
alembic -n local downgrade -1
alembic -n local downgrade base

# Show SQL without executing
alembic -n local upgrade head --sql
```

## ClickHouse-Specific Features

### Table Creation Examples
```sql
CREATE TABLE events (
    id UInt32,
    timestamp DateTime,
    user_id UInt32,
    event_type String,
    properties String
) 
ENGINE = MergeTree()
ORDER BY (timestamp, user_id)
PARTITION BY toYYYYMM(timestamp)
```

### Materialized View Patterns
```sql
CREATE MATERIALIZED VIEW daily_events_mv TO daily_events_table AS
SELECT 
    toDate(timestamp) as date,
    event_type,
    count() as event_count,
    uniq(user_id) as unique_users
FROM events
GROUP BY toDate(timestamp), event_type
```

### Dictionary Examples
```sql
CREATE DICTIONARY users_dict (
    id UInt32,
    name String,
    email String
)
PRIMARY KEY id
SOURCE(HTTP(
    url 'https://api.example.com/users'
    format 'JSONEachRow'
))
LIFETIME(600)
LAYOUT(FLAT())
```

## Advanced Features

### Multiple Database Support
Configure both ClickHouse and SQL Server migrations in the same project:

```yaml
migration:
  version_locations:
    clickhouse: "clickhouse_migrations"
    sql_server: "migrations"
```

### Custom Templates
Create your own migration templates in the `templates/` directory:

```python
# templates/custom_migration.py.template
"""Custom migration for {name}

Revision ID: {revision}
Revises: {down_revision}
"""

def upgrade():
    op.execute("-- Your custom SQL here")
```

Use with:
```bash
python generate.py custom my_template.py.template my_object
```

### Environment-Specific Schemas
Organize schemas by environment when needed:

```python
# schemas/shared.py - Common tables
# schemas/prod_only.py - Production-specific tables
```

## Project Structure

```
your-project/
├── config/
│   ├── config.yaml              # Main configuration
│   ├── examples/                # Configuration examples
│   └── templates/               # Config templates
├── schemas/
│   ├── __init__.py
│   ├── schema.py                # Your table definitions
│   └── clickhouse_sql/          # Raw SQL files
├── clickhouse_migrations/       # ClickHouse migration files
├── templates/                   # Migration templates
├── examples/                    # Reference implementations
├── alembic.ini                  # Generated Alembic config
├── env.py                       # Migration environment setup
├── generate.py                  # Migration generators
└── README.md                    # This file
```

## Validation & Testing

### Validate Configuration
```bash
python config/setup.py validate
```

### Test Migrations
```bash
# Test upgrade/downgrade cycle
alembic -n local upgrade head
alembic -n local downgrade base
alembic -n local upgrade head
```

### Dry Run
```bash
# See what SQL will be executed
alembic -n local upgrade head --sql
```

## Troubleshooting

### Common Issues

1. **Configuration not found**
   ```bash
   python config/setup.py init --template simple-local
   ```

2. **Connection errors**
   - Check your environment variables
   - Validate configuration: `python config/setup.py validate`
   - Test connection manually

3. **Template not found** 
   ```bash
   python generate.py list-templates
   ```

4. **Migration conflicts**
   - Use `alembic -n local history` to see migration chain
   - Resolve conflicts manually in migration files

### Getting Help

- Check the `examples/frost/` directory for a comprehensive real-world example
- Review migration templates in `templates/` 
- Validate your setup with `python config/setup.py validate`

## Examples

See the `examples/` directory for:
- **Frost Weather System** - Complete production implementation
- **Simple Analytics** - Basic time-series patterns  
- **E-commerce** - User and transaction tracking

---

## License & Attribution

This ClickHouse Migration Tool is created and maintained by **Dan Young**.

- **License:** MIT License (see LICENSE file)
- **Author:** Dan Young
- **Copyright:** © 2025 Dan Young

You are free to use, modify, and distribute this software under the terms of the MIT License. Attribution to the original author is appreciated but not required.

This tool was originally built for Frost's weather monitoring system and has been generalized for broader ClickHouse migration needs. The original Frost-specific implementation is preserved in `examples/frost/` as a comprehensive reference.
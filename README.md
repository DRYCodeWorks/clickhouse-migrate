# ClickHouse Tools

A comprehensive toolkit for managing multiple ClickHouse projects and environments. Perfect for teams working with ClickHouse Cloud across development, staging, and production environments.

## Features

- **Multi-project management**: Manage multiple ClickHouse projects from a single configuration
- **Environment separation**: Keep dev/staging/prod environments organized and secure
- **User & role management**: Standardized user creation and permission management
- **Query library**: Reusable SQL templates for common operations
- **Schema comparison**: Compare and sync schemas between environments
- **Connection pooling**: Efficient connection management with credential security
- **CLI interface**: Powerful command-line tools for daily operations

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url> clickhouse-tools
cd clickhouse-tools

# Install dependencies
pip install -r requirements.txt

# Make CLI executable
chmod +x ch.py
```

### 2. Configuration

```bash
# Copy environment template
cp .env.template .env

# Edit .env with your credentials
# NEVER commit .env to version control!

# Initialize your first project
python ch.py init myproject --environments dev,staging,prod
```

### 3. Basic Usage

```bash
# Test connections
python ch.py test --all

# Connect to a database
python ch.py connect metopio dev

# Run a query
python ch.py query metopio dev "SELECT count() FROM users"

# Execute a query file
python ch.py exec metopio dev queries/monitoring/table_sizes.sql

# List all projects and environments
python ch.py list
```

## Project Structure

```
clickhouse-tools/
├── ch.py                    # Main CLI tool
├── connection.py            # Connection management
├── users.py                 # User/role management
├── projects.yaml            # Project configuration
├── .env.template            # Environment variables template
├── requirements.txt         # Python dependencies
├── queries/                 # SQL query library
│   ├── admin/              # User and role queries
│   ├── monitoring/         # Performance and monitoring
│   ├── maintenance/        # Maintenance operations
│   └── templates/          # Table creation templates
├── sync_users.py           # User synchronization utility
├── compare_schemas.py      # Schema comparison utility
├── alembic/                # Database migrations (Alembic)
└── lambda-exporter/        # Lambda function for data exports
```

## CLI Commands

### Connection Management

```bash
# List all configured connections
python ch.py list

# Connect to a specific environment
python ch.py connect <project> <env>

# Test connections
python ch.py test <project> <env>
python ch.py test --all
```

### Query Execution

```bash
# Run an inline query
python ch.py query <project> <env> "SELECT 1"

# Execute query from file
python ch.py exec <project> <env> <file_path>

# Execute with parameters (coming soon)
python ch.py query <project> <env> --file query.sql --params '{"user_id": 123}'
```

### User Management

```bash
# Create a new user
python ch.py user create <project> <env> <username> --role developer_admin

# List all users
python ch.py user list <project> <env>

# Show user permissions
python ch.py user show <project> <env> <username>

# Copy user between environments
python ch.py user copy <project> <username> --from dev --to staging

# Sync all users
python ch.py user sync <project> --from dev --to staging
```

### Role Management

```bash
# List all roles
python ch.py role list <project> <env>

# Create a new role
python ch.py role create <project> <env> <role_name> --template service

# Show role permissions
python ch.py role show <project> <env> <role_name>
```

### Configuration

```bash
# Show current configuration
python ch.py config show

# Edit configuration
python ch.py config edit

# Validate configuration
python ch.py config validate
```

## Utility Scripts

### User Synchronization

Sync users between environments:

```bash
# Sync all users from dev to staging
python sync_users.py metopio dev staging

# Sync specific users
python sync_users.py metopio dev prod --users=user1,user2

# Dry run to see what would be synced
python sync_users.py metopio dev staging --dry-run
```

### Schema Comparison

Compare table schemas between environments:

```bash
# Compare all tables
python compare_schemas.py metopio dev prod

# Compare specific table
python compare_schemas.py metopio dev staging --table users

# Show detailed differences
python compare_schemas.py metopio staging prod --verbose

# Include CREATE TABLE statements
python compare_schemas.py metopio dev prod --show-create
```

## Query Library

Pre-built queries are organized in the `queries/` directory:

### Admin Queries
- `create_service_user.sql` - Create service users with proper roles
- `grant_roles.sql` - Grant roles to users
- `show_permissions.sql` - Display user permissions

### Monitoring Queries
- `check_compression.sql` - Check table compression ratios
- `table_sizes.sql` - Show table sizes and row counts
- `slow_queries.sql` - Find slow-running queries

### Templates
- `log_table_creation.sql` - Template for creating log tables

## Environment Variables

Configure credentials in `.env` file:

```bash
# Default settings
CH_DEFAULT_PROJECT=metopio
CH_DEFAULT_ENV=dev

# Project credentials
CH_METOPIO_DEV_USER=service_user
CH_METOPIO_DEV_PASSWORD=secret_password

CH_METOPIO_STAGING_USER=service_user
CH_METOPIO_STAGING_PASSWORD=secret_password

CH_METOPIO_PROD_USER=service_user
CH_METOPIO_PROD_PASSWORD=secret_password
```

## Security Best Practices

1. **Never commit credentials**: Add `.env` to `.gitignore`
2. **Use environment-specific users**: Different credentials per environment
3. **Principle of least privilege**: Grant only necessary permissions
4. **Regular audits**: Use `user show` and `role show` commands
5. **Secure password generation**: Use the built-in password generator
6. **Connection encryption**: Always use secure connections for ClickHouse Cloud

## Role Templates

The toolkit includes standard role templates:

- **developer_admin**: Full access to specific database for development
- **service**: Service account with read/write access
- **readonly**: Read-only access to database
- **analyst**: Read access with ability to create views
- **admin**: Full administrative access

## Working with Multiple Projects

### Adding a New Project

```bash
# Initialize new project
python ch.py init analytics --environments dev,prod

# Edit projects.yaml to add connection details
python ch.py config edit

# Test connections
python ch.py test analytics dev
python ch.py test analytics prod
```

### Switching Between Projects

```bash
# Use explicit project/env in commands
python ch.py query metopio dev "SELECT 1"
python ch.py query analytics prod "SELECT 1"

# Or set defaults in .env
CH_DEFAULT_PROJECT=analytics
CH_DEFAULT_ENV=prod
```

## Migrations with Alembic

The repository includes Alembic setup for managing database migrations:

```bash
cd alembic/
# Configure your database URL in alembic.ini
# Run migrations
alembic upgrade head
```

## Lambda Exporter

The `lambda-exporter/` directory contains a Lambda function for exporting data from databases to S3 as Parquet files. See [lambda-exporter/README.md](lambda-exporter/README.md) for details.

## Troubleshooting

### Connection Issues

```bash
# Test specific connection
python ch.py test <project> <env>

# Check credentials
env | grep CH_

# Verify ClickHouse Cloud is accessible
curl -v https://your-instance.clickhouse.cloud:8443/ping
```

### Permission Denied

```bash
# Check user permissions
python ch.py user show <project> <env> <username>

# Grant additional permissions
python ch.py role create <project> <env> temp_role
python ch.py query <project> <env> "GRANT SELECT ON db.* TO temp_role"
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Test thoroughly across environments
4. Submit a pull request

## Future Enhancements

- [ ] Migration management integration with Alembic
- [ ] Backup/restore functionality
- [ ] Query performance profiling
- [ ] Automated testing framework
- [ ] Web UI for management
- [ ] Terraform integration for infrastructure
- [ ] Audit logging
- [ ] Query result caching

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or contributions, please open an issue on GitHub.
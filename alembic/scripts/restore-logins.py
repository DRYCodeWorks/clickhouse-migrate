#!/usr/bin/env python3
"""
Script to restore SQL Server logins from AWS Secrets Manager after database restore.
Pulls passwords from secrets and creates CREATE LOGIN statements.
"""

import json
import sys
from typing import Dict, List

import boto3


# Map orphaned users to their secret names by environment
def get_user_secret_map(environment: str) -> Dict[str, str]:
    """Get user to secret mapping for specified environment."""
    base_secrets = {
        "alerts_handler": f"{environment}/mssql/alerts-handler",
        "api_authorizer_handler": f"{environment}/mssql/lambda-authorizer-user",
        "cv_handler": f"{environment}/mssql/cv-handler",
        "device_portal_api": f"{environment}/mssql/device-portal-api",
        "forecasts_handler": f"{environment}/mssql/forecast-ingestion-handler",
        "frost_api": (
            f"{environment}/mssql" if environment != "prod" else "prod/frost_api/mssql"
        ),
        "legacy_api": f"{environment}/mssql",
        "particle_handler": f"{environment}/mssql/particle-handler",
        "reports_handler": f"{environment}/mssql/reports-handler",
        "sds_handler": f"{environment}/mssql/sds-handler",
        "task_processor": f"{environment}/mssql",
        "vendor_feeds": f"{environment}/mssql",
    }
    return base_secrets


def get_secret_credentials(secret_name: str) -> tuple[str, str]:
    """Retrieve username and password from AWS Secrets Manager."""
    session = boto3.Session()
    client = session.client("secretsmanager")

    try:
        response = client.get_secret_value(SecretId=secret_name)
        secret = json.loads(response["SecretString"])
        username = secret.get("username", "")
        password = secret.get("password", "")
        return username, password
    except Exception as e:
        print(f"Error retrieving secret {secret_name}: {e}")
        return None, None


def generate_login_script(environment: str) -> str:
    """Generate SQL script to create logins."""
    user_secret_map = get_user_secret_map(environment)

    script_lines = [
        f"-- Auto-generated script to restore SQL Server logins for {environment} environment",
        "-- Run this against the master database",
        "",
    ]

    # Track actual usernames for the auto-fix commands
    actual_usernames = []

    for user, secret_name in user_secret_map.items():
        username, password = get_secret_credentials(secret_name)

        if password and username:
            script_lines.append(
                f"CREATE LOGIN [{username}] WITH PASSWORD = N'{password}';"
            )
            actual_usernames.append(username)

            # If the username from secret differs from mapped user, add a note
            if username != user:
                script_lines.append(
                    f"-- Note: Database user '{user}' maps to login '{username}'"
                )
        else:
            script_lines.append(
                f"-- MANUAL: CREATE LOGIN [{user}] WITH PASSWORD = 'REPLACE_WITH_PASSWORD';"
            )
            actual_usernames.append(user)  # fallback to expected name

    script_lines.extend(
        [
            "",
            "-- After creating logins, fix orphaned users by mapping them to the new logins:",
            "-- IMPORTANT: Run these commands against the TARGET DATABASE (not master)",
            "-- USE [your-database-name];",
            "",
        ]
    )

    # Generate ALTER USER statements to map database users to server logins
    for user, secret_name in user_secret_map.items():
        username, password = get_secret_credentials(secret_name)
        if username:
            script_lines.append(f"ALTER USER [{user}] WITH LOGIN = [{username}];")
        else:
            script_lines.append(
                f"-- MANUAL: ALTER USER [{user}] WITH LOGIN = [correct_login_name];"
            )

    return "\n".join(script_lines)


# Removed execute_login_creation function - only generating SQL scripts

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate SQL Server login restoration script from AWS Secrets Manager"
    )
    parser.add_argument(
        "--environment",
        "-e",
        required=True,
        choices=["dev", "stg", "prod"],
        help="Environment (dev, stg, prod)",
    )
    parser.add_argument(
        "--save-file", "-s", action="store_true", help="Also save to file"
    )

    args = parser.parse_args()

    script = generate_login_script(args.environment)
    print(script)

    if args.save_file:
        filename = f"restore_logins_{args.environment}.sql"
        with open(filename, "w") as f:
            f.write(script)
        print(f"\nScript saved to {filename}", file=sys.stderr)

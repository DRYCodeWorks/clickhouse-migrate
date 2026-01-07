"""
Schema module for ClickHouse migrations.

This module provides the metadata and schema loading functionality
for the ClickHouse migration system.
"""

import importlib
from pathlib import Path


def get_metadata(env=None):
    """
    Get SQLAlchemy metadata for the specified environment.
    
    Args:
        env: Environment name (not used in the basic template, but kept for compatibility)
        
    Returns:
        SQLAlchemy MetaData object
    """
    # Import the base schema module
    try:
        from schemas.schema import Base
        return Base.metadata
    except ImportError as e:
        # Provide helpful error message if schema module is missing
        schema_path = Path(__file__).parent / "schema.py"
        if not schema_path.exists():
            raise ImportError(
                f"Schema module not found at {schema_path}. "
                "Create a schema.py file with your table definitions, "
                "or run the setup tool to initialize basic templates."
            ) from e
        raise
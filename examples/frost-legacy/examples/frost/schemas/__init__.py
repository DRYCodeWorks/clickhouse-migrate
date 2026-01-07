"""
This module is responsible for maintaining everything related to SQLAlchemy modeling and orchestration.

Below you will see a few interesting bits:

1. MODULES is a constant which can be imported to point to shared_models elsewhere in the schemas module
2. get_metadata() is a helper function which gets called by the different {env}_schema.py files. 
3. implicitly_initialize_modules() is used to lazy load modules, so that we don't include metadata in the wrong env

"""

import importlib
from types import SimpleNamespace


def get_metadata(env):
    """
    Used to load only the subset of schema files necessary to orchestrate a migration for a single environment. This
    prevents metadata from leaking between environments, leading to incorrect revisions being created.
    """
    module = importlib.import_module(f".schema", package=__name__)
    return getattr(module, "Base").metadata

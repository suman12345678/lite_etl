"""northwind_dagster - the Dagster code location for the northwind_daily pipeline.

Package is named northwind_dagster (not `dagster`) so it never shadows the
installed `dagster` library on the import path. The repo directory is referred to
as "the dagster/ code location" in the design docs; this package is that.
"""

from northwind_dagster.definitions import defs

__all__ = ["defs"]

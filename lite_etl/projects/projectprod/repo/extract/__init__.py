"""Real extractor modules: extract/billing.py, extract/crm.py, extract/ref.py.

Each module lands rows into raw.* of the engine named by the ENGINE environment
variable (duckdb | databricks | snowflake). Every host/token/connection-string
value is read from os.environ -- see extract/common.py and ../README.md for the
full list of variables each extractor needs.
"""

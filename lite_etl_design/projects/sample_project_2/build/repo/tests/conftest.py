"""Shared pytest fixtures.

`bronze_db` builds a real DuckDB file with the committed fixtures loaded as
bronze.* (via demo/load.py) - the same loader the local demo and the
`dbt build --target ci` path use, so unit/integration tests and the demo agree.
"""

from __future__ import annotations

import duckdb
import pytest

from demo.load import load_fixtures_to_duckdb


@pytest.fixture
def bronze_db(tmp_path):
    """Path to a fresh DuckDB file with bronze.oltp__* and bronze.fx__rate loaded."""
    db = tmp_path / "test.duckdb"
    load_fixtures_to_duckdb(db, business_date="2026-09-08", run_id="test-run", dataset="good")
    return db


@pytest.fixture
def bronze_con(bronze_db):
    con = duckdb.connect(str(bronze_db))
    yield con
    con.close()

"""Load synthetic fixtures into a fresh DuckDB file as bronze.* tables.

Shared by `demo/run.py` and (in the real project) `tests/conftest.py`, so the
`dbt build --target ci` path and the demo path see the same bronze data.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb

REPO = Path(__file__).resolve().parents[1]
FIXTURES = REPO / "tests" / "fixtures"

# dataset name -> the OLTP fixture .sql that seeds customers/products/orders/order_lines
OLTP_FIXTURE = {
    "good": "oltp/sample.sql",
    "bad": "oltp/bad_rows.sql",
    "fixed": "oltp/bad_rows_fixed.sql",
}


def _audit_cols(con: duckdb.DuckDBPyConnection, table: str, source_file: str, run_id: str, ingest_date: str) -> None:
    con.execute(
        f"alter table {table} add column if not exists _run_id varchar; "
        f"alter table {table} add column if not exists _source_file varchar; "
        f"alter table {table} add column if not exists _extracted_at timestamp; "
        f"alter table {table} add column if not exists _ingest_date date;"
    )
    con.execute(
        f"update {table} set _run_id=?, _source_file=?, _extracted_at=?, _ingest_date=?",
        [run_id, source_file, datetime.now(timezone.utc), ingest_date],
    )


def load_fixtures_to_duckdb(db_path: str | Path, business_date: str, run_id: str, dataset: str = "good") -> None:
    """Create bronze.* in a fresh DuckDB file from the committed fixtures."""
    db_path = Path(db_path)
    if db_path.exists():
        db_path.unlink()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    con.execute("create schema if not exists bronze")

    # --- OLTP: run the fixture DDL/DML, then rename into bronze.oltp__* -----------
    oltp_sql = (FIXTURES / OLTP_FIXTURE[dataset]).read_text()
    con.execute(oltp_sql)
    for obj in ("customers", "products", "orders", "order_lines"):
        con.execute(f"create table bronze.oltp__{obj} as select * from {obj}")
        con.execute(f"drop table {obj}")
        _audit_cols(con, f"bronze.oltp__{obj}", OLTP_FIXTURE[dataset], run_id, business_date)

    # --- FX: flatten the rates map to (currency, rate_per_usd, rate_date) ---------
    fx = json.loads((FIXTURES / "fx" / "sample.json").read_text())
    rate_date = datetime.strptime(fx["time_last_update_utc"][:16], "%a, %d %b %Y").date().isoformat()
    con.execute("create table bronze.fx__rate(currency varchar, rate_per_usd double, rate_date date)")
    con.executemany(
        "insert into bronze.fx__rate values (?, ?, ?)",
        [(ccy, rate, rate_date) for ccy, rate in fx["rates"].items()],
    )
    _audit_cols(con, "bronze.fx__rate", "fx/sample.json", run_id, business_date)

    con.close()


def bronze_counts(db_path: str | Path) -> dict[str, int]:
    con = duckdb.connect(str(db_path), read_only=True)
    rows = con.execute(
        "select table_name, estimated_size from duckdb_tables() where schema_name='bronze' order by table_name"
    ).fetchall()
    out = {}
    for name, _ in rows:
        out[f"bronze.{name}"] = con.execute(f"select count(*) from bronze.{name}").fetchone()[0]
    con.close()
    return out

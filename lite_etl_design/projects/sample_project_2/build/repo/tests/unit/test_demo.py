"""Real tests for the runnable demo slice (load -> transform -> DQ -> reconcile).
These pass today; the 13 buildsheet stub tests alongside are still `skip`.
"""

from __future__ import annotations

from pathlib import Path

import duckdb

from demo import checks
from demo.run import main

SQL = Path(__file__).resolve().parents[2] / "demo" / "sql"


def _transform(con):
    con.execute((SQL / "10_staging.sql").read_text().replace("{salt}", "s"))
    con.execute((SQL / "20_marts.sql").read_text().replace("{run_id}", "r"))


def test_load_creates_bronze(bronze_con):
    assert bronze_con.execute("select count(*) from bronze.oltp__orders").fetchone()[0] == 4
    assert bronze_con.execute("select count(*) from bronze.fx__rate").fetchone()[0] == 4


def test_soft_deleted_customer_dropped_in_staging(bronze_con):
    _transform(bronze_con)
    assert bronze_con.execute("select count(*) from stg_oltp__customers").fetchone()[0] == 3


def test_no_raw_email_in_dim_customer(bronze_con):
    _transform(bronze_con)
    cols = [r[0] for r in bronze_con.execute("describe dim_customer").fetchall()]
    assert "email" not in cols and "email_clean" not in cols
    assert "email_hash" in cols


def test_dq_quarantines_negative_non_return(tmp_path):
    from demo.load import load_fixtures_to_duckdb

    db = tmp_path / "bad.duckdb"
    load_fixtures_to_duckdb(db, "2026-09-08", "r", dataset="bad")
    con = duckdb.connect(str(db))
    _transform(con)
    rej = con.execute("select order_id, reason_code from reject__fct_order").fetchall()
    assert rej == [(1005, "neg_gmv_non_return")]
    assert con.execute("select count(*) from fct_order where order_id = 1005").fetchone()[0] == 0


def test_reconciliation_checks_pass_on_good_data(bronze_con):
    _transform(bronze_con)
    r1 = checks.row_count_identity(bronze_con)
    r4 = checks.order_equals_lines(bronze_con)
    assert r1["verdict"] == "PASS"
    assert r4["verdict"] == "PASS"


def test_gate_blocks_and_exits_nonzero_on_control_mismatch():
    assert main(["--dataset", "bad", "--control-totals", "fail"]) == 1


def test_gate_publishes_on_pass():
    assert main(["--dataset", "good"]) == 0

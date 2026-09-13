"""Populate target/projectprod_ci.duckdb's `raw` schema with the same deterministic
fixture demo/load.py uses (single source of truth for the demo numbers), so
`dbt build --target ci` exercises the FULL model set against real rows -- not
just `dbt parse`. This stands in for extract/billing.py + extract/crm.py +
extract/ref.py, which land into this same `raw` schema in a real run.

    cd dbt && python seed_ci_raw.py && dbt deps && dbt seed --target ci && dbt build --target ci

(`make dbt-ci` runs all of this.)
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import duckdb  # noqa: E402

from demo import load as loader  # noqa: E402

DB_PATH = Path(__file__).resolve().parent / "target" / "projectprod_ci.duckdb"

_DDL = {
    "billing_invoices": """
        invoice_id varchar, account_id varchar, plan_code varchar, invoice_date varchar,
        currency varchar, amount_local double, status varchar, updated_at varchar
    """,
    "billing_subscriptions": """
        subscription_id varchar, account_id varchar, plan_code varchar,
        start_date varchar, end_date varchar, canceled_at varchar
    """,
    "crm_accounts": """
        account_id varchar, company_name varchar, billing_email varchar, country varchar,
        company_domain varchar, merged_into varchar, loaded_at varchar
    """,
    "ref_plans": """
        plan_code varchar, monthly_price_usd double, plan_tier varchar, is_retired integer
    """,
    "ref_fx_rates": """
        rate_date varchar, currency varchar, rate_to_usd double
    """,
}

_ROWS = {
    "billing_invoices": lambda scenario: loader._invoice_rows(scenario),
    "billing_subscriptions": lambda _scenario: loader._subscription_rows(),
    "crm_accounts": lambda _scenario: loader._account_rows(),
    "ref_plans": lambda _scenario: loader._plan_rows(),
    "ref_fx_rates": lambda _scenario: loader._fx_rows(),
}


def main(scenario: str = "clean") -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    con = duckdb.connect(str(DB_PATH))
    con.execute("create schema if not exists raw")
    for table, ddl in _DDL.items():
        con.execute(f"create table raw.{table} ({ddl})")
    for table, rows_fn in _ROWS.items():
        rows = rows_fn(scenario)
        if not rows:
            continue
        placeholders = ", ".join(["?"] * len(rows[0]))
        con.executemany(f"insert into raw.{table} values ({placeholders})", rows)
    con.close()
    print(f"seeded {DB_PATH} raw schema from demo/load.py fixtures (scenario={scenario})")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "clean")

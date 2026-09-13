"""Synthetic source data -> raw.* tables in a local SQLite database.

Stands in for extract/billing.py, extract/crm.py, extract/ref.py. Fully deterministic
(no random) so demo/data/control_totals.csv reconciles within tolerance on a clean run,
and the MRR movement identity ties out to the cent.

Scenarios (see demo/run.py):
  clean  - nothing wrong
  fail   - inject bad invoices (negative amount / unknown status / unknown plan);
           run.py additionally drops churn movements to break the MRR identity.
"""

from __future__ import annotations

import csv
import hashlib
import sqlite3
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"

PLAN_PRICE = {"BASIC": 50.0, "PRO": 150.0, "ENTERPRISE": 500.0}
PLAN_TIER = {"BASIC": "starter", "PRO": "growth", "ENTERPRISE": "enterprise"}
KNOWN_STATUS = ["draft", "open", "paid", "void", "uncollectible"]
MONTHS = ["2026-04", "2026-05", "2026-06", "2026-07"]
CURRENT_MONTH = "2026-07"

# account_id -> (country, currency)
ACCOUNT_GEO = {
    "A001": ("US", "USD"), "A002": ("DE", "EUR"), "A003": ("GB", "GBP"),
    "A004": ("US", "USD"), "A005": ("DE", "EUR"), "A006": ("GB", "GBP"),
    "A007": ("US", "USD"), "A008": ("DE", "EUR"), "A009": ("GB", "GBP"),
    "A010": ("US", "USD"), "A011": ("DE", "EUR"), "A012": ("GB", "GBP"),
}

# rate_to_usd, one row per currency per day (grain per spec: ref.fx_rates is
# "row (one per currency per day)"). We only need one quote per month for this
# fixture so each currency gets a rate dated the 1st of the month. GBP is MISSING
# for the current month ON PURPOSE -> the day-grain carry-forward join
# (currency, invoice_date) -> most recent prior rate_date must reuse July's value.
FX = {"USD": 1.00, "EUR": 1.08, "GBP": 1.27}

# (subscription_id, account_id, plan_code, start_date, end_date|None, canceled_at|None)
# start_date/end_date are month-aligned in this fixture (end_date = last day of the
# last active month) so the MRR proration factor in int_subscription_days always
# lands on 1.0 -- the proration SQL itself is real and handles a partial month, the
# demo data simply never exercises the fractional branch, same as project2's fixture.
SUBSCRIPTIONS = [
    ("S001", "A001", "BASIC", "2026-04-01", "2026-06-30", None),        # A001 upgrades ...
    ("S002", "A001", "PRO", "2026-07-01", None, None),                  #   ... to PRO in 07  -> expansion
    ("S003", "A002", "PRO", "2026-04-01", None, None),
    ("S004", "A003", "PRO", "2026-04-01", "2026-06-30", None),          # A003 downgrades ...
    ("S005", "A003", "BASIC", "2026-07-01", None, None),                #   ... to BASIC in 07 -> contraction
    ("S006", "A004", "ENTERPRISE", "2026-04-01", "2026-06-30", "2026-06-25"),  # A004 cancels -> churn in 07
    ("S007", "A005", "BASIC", "2026-07-01", None, None),                # brand new in 07      -> new
    ("S008", "A006", "BASIC", "2026-04-01", "2026-05-31", "2026-05-20"),  # A006 lapses ...
    ("S009", "A006", "BASIC", "2026-07-01", None, None),                #   ... then returns 07 -> reactivation
    ("S010", "A007", "PRO", "2026-05-01", None, None),                  # invoices land under merged id A013
    ("S011", "A008", "ENTERPRISE", "2026-04-01", None, None),
    ("S012", "A009", "BASIC", "2026-06-01", None, None),
    ("S013", "A010", "PRO", "2026-04-01", None, None),
    ("S014", "A011", "BASIC", "2026-04-01", None, None),
    ("S015", "A012", "PRO", "2026-07-01", None, None),                  # brand new in 07      -> new
]


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _month_le(a: str, b: str) -> bool:
    return a <= b  # 'YYYY-MM' strings sort chronologically


def _active(sub, month: str) -> bool:
    _, _, _, start, end, _canceled = sub
    start_m, end_m = start[:7], (end[:7] if end else None)
    return _month_le(start_m, month) and (end_m is None or _month_le(month, end_m))


def _account_rows() -> list[tuple]:
    rows = []
    for aid, (country, _cur) in ACCOUNT_GEO.items():
        n = int(aid[1:])
        rows.append((aid, f"Company {n} Ltd", f"ap{n}@corp{n}.example.com", country,
                     "corp%d.example.com" % n, None, "2026-07-01T00:00:00"))
    # A013 was merged into A007 - old id still shows up in the daily CRM snapshot
    rows.append(("A013", "Company 7 (old)", "billing@corp7-old.example.com", "US",
                 "corp7-old.example.com", "A007", "2026-07-01T00:00:00"))
    return rows


def _plan_rows() -> list[tuple]:
    return [(code, PLAN_PRICE[code], PLAN_TIER[code], 0) for code in PLAN_PRICE]


def _fx_rows() -> list[tuple]:
    rows = []
    for m in MONTHS:
        for cur, rate in FX.items():
            if cur == "GBP" and m == CURRENT_MONTH:
                continue  # gap on purpose -> carry forward
            rows.append((f"{m}-01", cur, rate))
    return rows


def _invoice_rows(scenario: str) -> list[tuple]:
    rows = []
    seq = 0
    for sub in SUBSCRIPTIONS:
        sub_id, account_id, plan_code, _start, _end, _canceled = sub
        raw_account = "A013" if sub_id == "S010" else account_id
        _country, currency = ACCOUNT_GEO[account_id]
        price = PLAN_PRICE[plan_code]
        rate = FX[currency]
        amount_local = round(price / rate, 2)
        for m in MONTHS:
            if not _active(sub, m):
                continue
            seq += 1
            inv = f"INV{seq:05d}"
            rows.append((inv, raw_account, plan_code, f"{m}-05", currency, amount_local,
                         "paid", f"{m}-05T09:00:00"))

    # one webhook retry: same invoice_id re-sent later with a newer updated_at
    first = rows[0]
    rows.append((first[0], first[1], first[2], first[3], first[4], first[5],
                 first[6], f"{first[3][:7]}-18T22:00:00"))

    if scenario == "fail":
        seq += 1
        rows.append((f"INV{seq:05d}", "A002", "PRO", f"{CURRENT_MONTH}-06", "EUR", -138.89,
                     "paid", f"{CURRENT_MONTH}-06T09:00:00"))          # negative amount
        seq += 1
        rows.append((f"INV{seq:05d}", "A003", "BASIC", f"{CURRENT_MONTH}-06", "GBP", -39.37,
                     "paid", f"{CURRENT_MONTH}-06T09:00:00"))          # negative amount
        seq += 1
        rows.append((f"INV{seq:05d}", "A008", "ENTERPRISE", f"{CURRENT_MONTH}-06", "EUR", 462.96,
                     "bogus", f"{CURRENT_MONTH}-06T09:00:00"))         # status not in enum
        seq += 1
        rows.append((f"INV{seq:05d}", "A011", "PROMO_2024", f"{CURRENT_MONTH}-06", "EUR", 0.00,
                     "void", f"{CURRENT_MONTH}-06T09:00:00"))          # plan_code not in dim_plan (warn)
    return rows


def _subscription_rows() -> list[tuple]:
    return [(s[0], s[1], s[2], s[3], s[4], s[5]) for s in SUBSCRIPTIONS]


def load(db_path: Path, scenario: str = "clean") -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    con.executescript(
        """
        drop table if exists raw_billing_invoices;
        drop table if exists raw_billing_subscriptions;
        drop table if exists raw_crm_accounts;
        drop table if exists raw_ref_plans;
        drop table if exists raw_ref_fx_rates;

        create table raw_billing_invoices (
            invoice_id text, account_id text, plan_code text, invoice_date text,
            currency text, amount_local real, status text, updated_at text
        );
        create table raw_billing_subscriptions (
            subscription_id text, account_id text, plan_code text,
            start_date text, end_date text, canceled_at text
        );
        create table raw_crm_accounts (
            account_id text, company_name text, billing_email text, country text,
            company_domain text, merged_into text, loaded_at text
        );
        create table raw_ref_plans (
            plan_code text, monthly_price_usd real, plan_tier text, is_retired integer
        );
        create table raw_ref_fx_rates (
            rate_date text, currency text, rate_to_usd real
        );
        """
    )
    con.executemany("insert into raw_billing_invoices values (?,?,?,?,?,?,?,?)", _invoice_rows(scenario))
    con.executemany("insert into raw_billing_subscriptions values (?,?,?,?,?,?)", _subscription_rows())
    con.executemany("insert into raw_crm_accounts values (?,?,?,?,?,?,?)", _account_rows())
    con.executemany("insert into raw_ref_plans values (?,?,?,?)", _plan_rows())
    con.executemany("insert into raw_ref_fx_rates values (?,?,?)", _fx_rows())
    con.commit()
    con.close()


def read_control_totals() -> dict[str, float]:
    with open(DATA / "control_totals.csv", newline="") as fh:
        return {r["metric"]: float(r["expected_value"]) for r in csv.DictReader(fh)}


def raw_counts(db_path: Path) -> dict[str, int]:
    con = sqlite3.connect(db_path)
    out = {
        t: con.execute(f"select count(*) from {t}").fetchone()[0]
        for t in ("raw_billing_invoices", "raw_billing_subscriptions", "raw_crm_accounts",
                  "raw_ref_plans", "raw_ref_fx_rates")
    }
    con.close()
    return out

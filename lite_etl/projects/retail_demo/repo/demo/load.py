"""Synthetic source data -> raw.* tables in a local SQLite database.

Stands in for `extract/oltp` and `extract/fx`. Deterministic (fixed seed) so the
finance control totals in demo/data/control_totals.csv always reconcile on a clean run.

Scenarios (see demo/run.py):
  clean  - nothing wrong
  fail   - inject 3 negative-amount 'store' orders (-> quarantine) and leave the
           finance control total untouched; run.py perturbs it to force a BLOCK.
"""

from __future__ import annotations

import csv
import hashlib
import random
import sqlite3
from datetime import date, timedelta
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"

# rate_to_usd: how many USD one unit of the currency is worth
CURRENCIES = {"USD": 1.00, "EUR": 1.08, "GBP": 1.27, "INR": 0.012, "JPY": 0.0067}
KNOWN_CURRENCIES = sorted(CURRENCIES)
CHANNELS = ["web", "store", "wholesale"]
BUSINESS_DAYS = [date(2026, 9, 1) + timedelta(days=i) for i in range(7)]  # Tue..Mon


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _fx_rows() -> list[tuple]:
    """One rate per currency per day, but SKIP the weekend (Sat 5th, Sun 6th) to
    exercise the carry-forward join."""
    rows = []
    for d in BUSINESS_DAYS:
        if d.weekday() >= 5:  # 5=Sat, 6=Sun -> gap on purpose
            continue
        for cur, rate in CURRENCIES.items():
            rows.append((d.isoformat(), cur, rate))
    return rows


def _customer_rows() -> list[tuple]:
    rows = []
    for i in range(1, 21):
        cid = f"C{i:03d}"
        if i <= 3:
            email = f"tester{i}@example.test"        # test rows -> dropped in staging
        else:
            email = f"user{i}@shop.example.com"
        name = f"Customer {i}"
        country = ["US", "DE", "GB", "IN", "JP"][i % 5]
        rows.append((cid, name, email, country, "2026-08-01T00:00:00"))
    return rows


def _order_rows(scenario: str) -> list[tuple]:
    rng = random.Random(42)
    rows = []
    oid = 0
    for d in BUSINESS_DAYS:
        for _ in range(30):
            oid += 1
            cust = f"C{rng.randint(1, 20):03d}"
            channel = rng.choice(CHANNELS)
            currency = rng.choices(KNOWN_CURRENCIES, weights=[5, 3, 3, 2, 2])[0]
            # amount scaled so every currency lands near a few hundred USD
            usd_target = rng.uniform(50, 400)
            amount_local = round(usd_target / CURRENCIES[currency], 2)
            ts = f"{d.isoformat()}T{rng.randint(8, 20):02d}:{rng.randint(0, 59):02d}:00"
            rows.append((f"O{oid:05d}", cust, channel, currency, amount_local, ts, ts))

    # a duplicate re-send with a newer loaded_at (dedupe keeps this one)
    first = rows[0]
    rows.append((first[0], first[1], first[2], first[3], round(first[4] + 10, 2),
                 first[5], "2026-09-08T02:00:00"))

    if scenario == "fail":
        # 3 refund-shaped rows that slipped through with negative totals, on 'store'
        # (a different channel from the 'web' reconcile) -> pure quarantine demo.
        for k in range(3):
            oid += 1
            rows.append((f"O{oid:05d}", "C005", "store", "USD", -75.0 - k,
                         "2026-09-04T12:00:00", "2026-09-04T12:00:00"))
    return rows


def load(db_path: Path, scenario: str = "clean") -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys=ON")

    con.executescript(
        """
        drop table if exists raw_orders;
        drop table if exists raw_customers;
        drop table if exists raw_fx_rates;

        create table raw_orders (
            order_id text, customer_id text, channel text, currency text,
            amount_local real, order_ts text, loaded_at text
        );
        create table raw_customers (
            customer_id text, full_name text, email text, country text, loaded_at text
        );
        create table raw_fx_rates (
            rate_date text, currency text, rate_to_usd real
        );
        """
    )
    con.executemany("insert into raw_orders values (?,?,?,?,?,?,?)", _order_rows(scenario))
    con.executemany("insert into raw_customers values (?,?,?,?,?)", _customer_rows())
    con.executemany("insert into raw_fx_rates values (?,?,?)", _fx_rows())
    con.commit()
    con.close()


def read_control_totals() -> dict[str, float]:
    with open(DATA / "control_totals.csv", newline="") as fh:
        return {r["channel"]: float(r["expected_net_usd"]) for r in csv.DictReader(fh)}


def raw_counts(db_path: Path) -> dict[str, int]:
    con = sqlite3.connect(db_path)
    out = {
        t: con.execute(f"select count(*) from {t}").fetchone()[0]
        for t in ("raw_orders", "raw_customers", "raw_fx_rates")
    }
    con.close()
    return out

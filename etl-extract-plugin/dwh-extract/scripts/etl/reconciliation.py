"""Reconciliation: prove the landed dataset agrees with the source.

Checks (each -> PASS/FAIL with expected vs actual):
  1. row_conservation            extracted == written + rejected
  2. min_rows_written            written >= expect_min_rows
  3. control_total_conservation  sum(landed) + sum(rejected) == source total (from manifest)
  4. source_stability            re-reading the source now gives the same total
  5. landed_key_not_null         key columns are populated in data.csv
  6. data_file_present           data.csv exists
"""
from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from .extractors import get_extractor


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _col_sum(rows, col) -> tuple[float, int]:
    total, n = 0.0, 0
    for r in rows:
        try:
            total += float(r.get(col))
            n += 1
        except (TypeError, ValueError):
            pass
    return total, n


def _read_csv(path: Path) -> list[dict]:
    path = Path(path)
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def reconcile(source, manifest: dict, run_path: Path) -> dict:
    run_path = Path(run_path)
    checks: list[dict] = []

    def add(check, ok, expected, actual, detail=""):
        checks.append({
            "check": check,
            "status": "PASS" if ok else "FAIL",
            "expected": expected,
            "actual": actual,
            "detail": detail,
        })

    rc = source.reconciliation or {}
    extracted = manifest["rows_extracted"]
    written = manifest["rows_written"]
    rejected = manifest["rows_rejected"]

    add("row_conservation", extracted == written + rejected,
        extracted, written + rejected, f"{written} written + {rejected} rejected")

    min_rows = rc.get("expect_min_rows", 1)
    add("min_rows_written", written >= min_rows, f">={min_rows}", written)

    col = rc.get("control_total_column")
    tol = float(rc.get("tolerance", 0.01))
    if col:
        landed_total, _ = _col_sum(_read_csv(run_path / "data.csv"), col)
        rej_total, _ = _col_sum(_read_csv(run_path / "rejects.csv"), col)
        src_total = (manifest.get("control_totals") or {}).get(col)
        got = round(landed_total + rej_total, 6)
        ok = src_total is not None and abs(got - src_total) <= tol
        add(f"control_total_conservation[{col}]", ok, src_total, got,
            f"landed {round(landed_total, 4)} + rejected {round(rej_total, 4)}; tol {tol}")

        fresh_total, n = _col_sum(get_extractor(source).extract(), col)
        add(f"source_stability[{col}]",
            src_total is not None and abs(round(fresh_total, 6) - src_total) <= tol,
            src_total, round(fresh_total, 6), f"re-read {n} source values")

    keys = rc.get("key_columns", [])
    if keys:
        landed = _read_csv(run_path / "data.csv")
        bad = sum(1 for r in landed if any(not str(r.get(k, "")).strip() for k in keys))
        add("landed_key_not_null", bad == 0, 0, bad, f"columns {keys}")

    data_path = run_path / "data.csv"
    add("data_file_present", data_path.exists(), True, data_path.exists())

    status = "PASS" if all(c["status"] == "PASS" for c in checks) else "FAIL"
    return {
        "source": source.name,
        "run_id": manifest["run_id"],
        "status": status,
        "checks": checks,
        "data_sha256": _sha256(data_path) if data_path.exists() else None,
    }

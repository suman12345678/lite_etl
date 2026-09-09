"""Orchestrator for one extraction run:

    extract -> business rules -> land -> manifest -> reconcile

Everything downstream (the warehouse load) keys off the run_id and the
_manifest.json / _reconciliation.json that land next to the data.
"""
from __future__ import annotations

from pathlib import Path

from . import landing
from .business_rules import apply_rules
from .extractors import get_extractor
from .reconciliation import reconcile


def _control_totals(rows: list[dict], columns: list[str]) -> dict:
    totals = {}
    for col in columns:
        s = 0.0
        for r in rows:
            try:
                s += float(r.get(col))
            except (TypeError, ValueError):
                pass
        totals[col] = round(s, 6)
    return totals


def run_extraction(source, landing_zone: Path, now=None) -> dict:
    now = now or landing.utcnow()
    run_id = landing.new_run_id(now)
    target = landing.run_dir(landing_zone, source.name, run_id, now)
    started = landing.utcnow()

    # 1. Extract (raw, untouched rows)
    raw_rows = get_extractor(source).extract()

    ctl_cols = []
    if source.reconciliation.get("control_total_column"):
        ctl_cols.append(source.reconciliation["control_total_column"])
    control_totals = _control_totals(raw_rows, ctl_cols)

    # 2. Business rules (work on copies so raw counts stay honest)
    clean_rows, rejected, applied = apply_rules(
        [dict(r) for r in raw_rows], source.business_rules
    )

    # 3. Land
    data_path = landing.write_dataset(target, clean_rows, "data.csv")
    if rejected:
        landing.write_dataset(target, rejected, "rejects.csv", include_private=True)

    # 4. Manifest
    finished = landing.utcnow()
    manifest = {
        "run_id": run_id,
        "source": source.name,
        "source_type": source.type,
        "extract_mode": source.extract.get("mode", "full"),
        "started_utc": started.isoformat(),
        "finished_utc": finished.isoformat(),
        "rows_extracted": len(raw_rows),
        "rows_written": len(clean_rows),
        "rows_rejected": len(rejected),
        "business_rules_applied": applied,
        "control_totals": control_totals,
        "landing_path": str(target),
        "data_file": str(data_path),
    }
    landing.write_json(target, "_manifest.json", manifest)

    # 5. Reconcile
    report = reconcile(source, manifest, target)
    landing.write_json(target, "_reconciliation.json", report)

    landing.append_run_log(landing_zone, {
        "run_id": run_id,
        "source": source.name,
        "finished_utc": manifest["finished_utc"],
        "rows_written": manifest["rows_written"],
        "rows_rejected": manifest["rows_rejected"],
        "reconciliation": report["status"],
        "landing_path": str(target),
    })

    return {"manifest": manifest, "reconciliation": report}

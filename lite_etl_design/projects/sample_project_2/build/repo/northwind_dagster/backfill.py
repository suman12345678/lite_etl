"""Backfill entrypoint for northwind_daily.

Re-runs a [from, to] window: the ingest assets first, then curated_build +
downstream over the same range. One run_id per business date, OLDEST FIRST; each
date's watermark advances only on its own reconcile PASS. Backfill is capped at
3 concurrent dates (Dagster concurrency). The go-live 12/24-month load (Q2) runs
on the prd on-demand pool over a weekend window.

This is a thin wrapper documenting the supported invocation; the actual backfill
is launched via the Dagster CLI / UI.

    # ingest assets, oldest first:
    dagster job backfill --job pos_ingest_job \
        --partition-range 2024-01-01...2024-12-31

    # then curated_build + reconcile + publish over the same range:
    dagster job backfill --job curated_build_job \
        --partition-range 2024-01-01...2024-12-31

Phase 4 scaffold - see pipeline/orchestration-wiring.md "Backfill entrypoint".
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta

MAX_CONCURRENT_DATES = 3


def daterange(start: date, end: date):
    for n in range((end - start).days + 1):
        yield start + timedelta(days=n)


def main() -> None:
    p = argparse.ArgumentParser(description="Print the Dagster backfill plan for a window.")
    p.add_argument("--from", dest="frm", required=True, type=date.fromisoformat)
    p.add_argument("--to", dest="to", required=True, type=date.fromisoformat)
    args = p.parse_args()
    dates = list(daterange(args.frm, args.to))
    print(f"{len(dates)} business dates, oldest first, <= {MAX_CONCURRENT_DATES} concurrent:")
    for d in dates:
        print(f"  {d.isoformat()}  ingest -> curated_build -> reconcile -> publish")
    # TODO: optionally shell out to `dagster job backfill ...` for each job.


if __name__ == "__main__":
    main()

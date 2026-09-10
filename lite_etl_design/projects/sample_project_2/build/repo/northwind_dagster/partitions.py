"""Business-date partitions (UTC). Every northwind_daily asset is keyed by D.
Phase 4 scaffold - see pipeline/orchestration-wiring.md.
"""

from __future__ import annotations

from dagster import DailyPartitionsDefinition

# TODO set the real go-live start date (Q2: 12 vs 24 month backfill depth).
DAILY = DailyPartitionsDefinition(
    start_date="2024-01-01",   # TODO
    timezone="UTC",
    end_offset=0,
)

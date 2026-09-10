"""Schedules for northwind_daily. One per ingest cron (all UTC) + the
curated_build kick-off once the day's ingest assets are fresh.

Phase 4 scaffold - see pipeline/orchestration-wiring.md "Triggers".
"""

from __future__ import annotations

from dagster import (
    AssetSelection,
    RunRequest,
    ScheduleDefinition,
    define_asset_job,
    schedule,
)

from northwind_dagster.assets.ingest import SOURCES

# --- ingest schedules (pos also has the S3 sensor as its primary trigger) -------
_ingest_schedules = [
    ScheduleDefinition(
        name=f"{name}_schedule",
        job=define_asset_job(f"{name}_job", selection=AssetSelection.assets(name)),
        cron_schedule=cron,
        execution_timezone="UTC",
    )
    for _src, (name, cron) in SOURCES.items()
]

# --- curated_build + downstream, daily 05:15 UTC --------------------------------
curated_job = define_asset_job(
    "curated_build_job",
    selection=AssetSelection.assets("curated_build").downstream(),  # -> reconcile check -> publish -> ...
)


@schedule(job=curated_job, cron_schedule="15 5 * * *", execution_timezone="UTC")
def curated_build_schedule(context):
    # TODO: guard on all six ingest assets being fresh for context.scheduled_execution_time's D
    #   (freshness check / AutoMaterializePolicy). Early-warning alert if not done by 05:45;
    #   SLA breach alert at 06:00 if _SUCCESS absent.
    d = context.scheduled_execution_time.date().isoformat()
    return RunRequest(run_key=f"curated-{d}", partition_key=d)


ALL_SCHEDULES = [*_ingest_schedules, curated_build_schedule]

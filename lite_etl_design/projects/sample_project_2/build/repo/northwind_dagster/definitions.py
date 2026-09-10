"""Dagster code location for northwind_daily. Phase 4 scaffold - see
pipeline/orchestration-wiring.md. Structure + edges + retries + the blocking
reconcile check are wired; bodies are TODO against the Phase 3 components.
"""

from __future__ import annotations

from dagster import Definitions

from northwind_dagster.assets.ingest import ingest_assets
from northwind_dagster.assets.publish import (
    advance_watermarks,
    catalog_register,
    emit_metrics,
    publish,
)
from northwind_dagster.assets.transform import curated_build
from northwind_dagster.checks.reconcile import reconcile
from northwind_dagster.resources import RESOURCES
from northwind_dagster.schedules import ALL_SCHEDULES
from northwind_dagster.sensors import pos_s3_sensor

defs = Definitions(
    assets=[
        *ingest_assets,          # oltp/shopify/pos/salesforce/ga4/fx -> bronze
        curated_build,           # @dbt_assets - staging+ intermediate+ marts+ (exclude tag:recon)
        publish,
        catalog_register,
        advance_watermarks,
        emit_metrics,
    ],
    asset_checks=[reconcile],    # blocking check on the curated_build gold assets
    schedules=ALL_SCHEDULES,
    sensors=[pos_s3_sensor],
    resources=RESOURCES,
)

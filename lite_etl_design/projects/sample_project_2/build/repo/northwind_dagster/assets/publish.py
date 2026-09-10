"""Post-gate assets: publish -> catalog_register -> advance_watermarks, plus
emit_metrics. None of these materialise unless the blocking `reconcile` check
passed (Dagster enforces this for blocking checks on the upstream gold assets).

Phase 4 scaffold - see pipeline/orchestration-wiring.md rows 12-16.
"""

from __future__ import annotations

from dagster import AssetExecutionContext, RetryPolicy, asset

from northwind_dagster.assets.transform import curated_build
from northwind_dagster.partitions import DAILY


@asset(
    partitions_def=DAILY,
    deps=[curated_build],
    retry_policy=RetryPolicy(max_retries=2),
    required_resource_keys={"settings", "databricks", "s3"},
    compute_kind="python",
)
def publish(context: AssetExecutionContext) -> None:
    d = context.partition_key
    # TODO: from publish.publish import run; run(d, context.run_id, target=<env>)
    #   one transaction per table group per D into gold / gold_pii; re-publish = no-op merge.
    raise NotImplementedError(f"publish {d}")


@asset(
    partitions_def=DAILY,
    deps=[publish],
    retry_policy=RetryPolicy(max_retries=2),
    required_resource_keys={"settings", "databricks", "s3", "alerts"},
    compute_kind="python",
)
def catalog_register(context: AssetExecutionContext) -> None:
    d = context.partition_key
    # TODO: from publish.catalog import register; UC tags + comments + lineage + write _SUCCESS.
    #   on fail: warn + async retry (do not block).
    raise NotImplementedError(f"catalog_register {d}")


@asset(
    partitions_def=DAILY,
    deps=[catalog_register],
    retry_policy=RetryPolicy(max_retries=1),
    required_resource_keys={"settings", "databricks"},
    compute_kind="python",
)
def advance_watermarks(context: AssetExecutionContext) -> None:
    d = context.partition_key
    # TODO: from extractors.common.state import advance; advance the 6 source watermarks for D.
    #   only reached because reconcile PASSED and catalog_register succeeded. Manual on fail.
    raise NotImplementedError(f"advance_watermarks {d}")


@asset(
    partitions_def=DAILY,
    deps=[publish],
    retry_policy=RetryPolicy(max_retries=1),
    required_resource_keys={"settings", "alerts"},
    compute_kind="python",
)
def emit_metrics(context: AssetExecutionContext) -> None:
    d = context.partition_key
    # TODO: from obs.metrics import emit + Elementary report. Warn on fail.
    raise NotImplementedError(f"emit_metrics {d}")

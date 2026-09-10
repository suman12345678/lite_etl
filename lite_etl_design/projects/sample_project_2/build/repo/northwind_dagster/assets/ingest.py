"""Ingest assets: one per source, partitioned by business date D, group "ingest".
Each calls the Phase 3 extractor (extractors.<src>.run) which lands raw rows +
manifest in bronze. Retry 3 / expo 30s,2m,8m (transient). Permanent failure =>
stop + page (failure hook / alert resource).

Phase 4 scaffold - see pipeline/orchestration-wiring.md rows 1-7.
"""

from __future__ import annotations

from dagster import AssetExecutionContext, Backoff, RetryPolicy, asset

from northwind_dagster.partitions import DAILY

TRANSIENT_RETRY = RetryPolicy(max_retries=3, delay=30, backoff=Backoff.EXPONENTIAL)  # 30s, 2m, 8m

# source key -> (asset name, cron). pos is sensor-driven + a 04:00 sweep backstop.
SOURCES = {
    "oltp": ("oltp_ingest", "0 */4 * * *"),
    "shopify": ("shopify_ingest", "0 * * * *"),
    "pos": ("pos_ingest", "0 4 * * *"),
    "salesforce": ("salesforce_ingest", "0 */6 * * *"),
    "ga4": ("ga4_ingest", "0 4 * * *"),           # D-2 shard
    "fx": ("fx_ingest", "0 5 * * *"),
}


def _make_ingest_asset(src: str, name: str):
    @asset(
        name=name,
        group_name="ingest",
        partitions_def=DAILY,
        retry_policy=TRANSIENT_RETRY,
        required_resource_keys={"settings", "secrets", "s3", "alerts"},
        compute_kind="python",
    )
    def _ingest(context: AssetExecutionContext) -> None:
        business_date = context.partition_key
        # TODO:
        #   from extractors.<src> import run
        #   run(date=business_date, settings=context.resources.settings)
        #   -> bronze.<src>__*, new run_id, manifest.json in _manifests/
        # POS: parse + supersede prior _file_etag for (store, D).
        # GA4: skip + retry next cycle if the D-2 shard is not final (48h budget).
        raise NotImplementedError(f"{src} ingest for {business_date}")

    return _ingest


ingest_assets = [_make_ingest_asset(src, name) for src, (name, _cron) in SOURCES.items()]

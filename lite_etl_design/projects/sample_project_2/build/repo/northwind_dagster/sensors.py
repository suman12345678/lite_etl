"""pos_s3_sensor: fire pos_ingest when a POS file lands in the inbound bucket.

Primary trigger for POS (files arrive 02:00-03:30 UTC); the `0 4 * * *`
pos_ingest schedule in schedules.py is the sweep backstop. Key template:
pos/dt={date}/store={store}/txns.csv.gz (config: sources.pos.key_template).

Phase 4 scaffold - see pipeline/orchestration-wiring.md "Triggers".
"""

from __future__ import annotations

from dagster import AssetSelection, RunRequest, SkipReason, define_asset_job, sensor

pos_ingest_job = define_asset_job("pos_ingest_job", selection=AssetSelection.assets("pos_ingest"))


@sensor(job=pos_ingest_job, minimum_interval_seconds=60)
def pos_s3_sensor(context):
    # TODO: list new objects under s3://northwind-<env>-inbound/pos/ since the cursor
    #   (S3 event notification -> SQS is the production path; polling shown here).
    #   Parse (dt, store) from the key; one RunRequest per (store, dt) partition.
    #   Supersede handling (new _file_etag for an existing (dt, store)) is in the extractor.
    new_keys: list[str] = []  # TODO
    if not new_keys:
        return SkipReason("no new POS files")
    for key in new_keys:
        dt = key.split("dt=")[1].split("/")[0]     # TODO robust parse
        yield RunRequest(run_key=key, partition_key=dt)

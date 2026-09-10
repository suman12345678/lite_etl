"""curated_build: the dbt project loaded as Dagster assets via dagster-dbt.

Runs `dbt build --select staging+ intermediate+ marts+ --exclude tag:recon`
against the day's bronze once source_freshness + schema_drift pass. Retry 1
(Spark executor loss only). Concurrency key limits it to 1 per env.
The gold assets it produces are what checks/reconcile.py gates.

Phase 4 scaffold - see pipeline/orchestration-wiring.md rows 8-10.
"""

from __future__ import annotations

from pathlib import Path

from dagster import AssetExecutionContext, RetryPolicy
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

# TODO point at the packaged manifest.json produced by `dbt parse` in CI.
DBT_PROJECT = DbtProject(project_dir=Path(__file__).parents[2] / "dbt")
DBT_PROJECT.prepare_if_dev()

EXECUTOR_LOSS_RETRY = RetryPolicy(max_retries=1)


@dbt_assets(
    manifest=DBT_PROJECT.manifest_path,
    exclude="tag:recon",                       # recon runs in the blocking check, not here
    retry_policy=EXECUTOR_LOSS_RETRY,
    op_tags={"dagster/concurrency_key": "curated_build"},   # max 1 per env
)
def curated_build(context: AssetExecutionContext, dbt: DbtCliResource):
    business_date = context.partition_key
    # source_freshness + schema_drift are modelled as upstream gate assets (TODO:
    # add as @asset stubs or dbt source-freshness op); on drift => halt+ticket+page.
    yield from dbt.cli(
        [
            "build",
            "--select", "staging+ intermediate+ marts+",
            "--exclude", "tag:recon",
            "--vars", f"{{business_date: {business_date}, run_id: {context.run_id}}}",
            # "--defer", "--state", "<prd manifest>",   # slim CI only
        ],
        context=context,
    ).stream()

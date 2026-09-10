"""The reconciliation gate as a BLOCKING Dagster asset check.

Wraps the Phase 3 recon/gate.py::run_gate (dbt test --select tag:recon +
recon.compare manifest compare). verdict != "PASS" => AssetCheckResult(passed=
False); because blocking=True, publish / catalog_register / advance_watermarks
never materialise, the run exits non-zero, no _SUCCESS is written, watermarks are
untouched, and PagerDuty fires with the _reconciliation.json link.

Phase 4 scaffold - see pipeline/orchestration-wiring.md row 11 + design/component-design.md.
"""

from __future__ import annotations

from datetime import date

from dagster import AssetCheckResult, AssetCheckSeverity, asset_check

from northwind_dagster.assets.transform import curated_build


@asset_check(
    asset=curated_build,          # TODO narrow to the specific gold.* / gold_pii.* table-group assets
    blocking=True,
    required_resource_keys={"settings", "databricks", "s3", "alerts"},
    description="05 reconciliation: row-count identity, per-channel GMV vs control totals (+/-0.5%), "
    "refund balancing + linkage, order = sum(lines), FX coverage, duplicate keys, "
    "distribution drift vs 28-day baseline (warn 30% / fail 60%), PII-leak scan.",
)
def reconcile(context) -> AssetCheckResult:
    business_date = date.fromisoformat(context.partition_key) if context.has_partition_key else date.today()
    # from recon.gate import run_gate
    # result = run_gate(business_date, context.run_id, target=context.resources.settings.env,
    #                   settings=context.resources.settings)
    # passed = result.verdict == "PASS"
    # if not passed:
    #     context.resources.alerts.page("reconcile FAIL", links=[result.report_uri])
    # return AssetCheckResult(
    #     passed=passed,
    #     severity=AssetCheckSeverity.ERROR,
    #     metadata={"report_uri": result.report_uri,
    #               "failed_checks": [c.name for c in result.checks if c.verdict != "PASS"]},
    # )
    raise NotImplementedError(f"reconcile gate for {business_date}")

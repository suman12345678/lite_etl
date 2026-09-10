# Environments & config

> Phase 4 deliverable. The environment matrix and how configuration is layered so
> the same artefact runs everywhere. From `requirements/09` + `10` and
> `design/deployment-and-iac.md` s.8.

## Environment matrix

| | _(one column per canonical env in `requirements/10`, e.g. dev, stg, prd)_ | | |
|---|-----|-----------|------|
| Warehouse account / workspace | | | |
| Catalog / database | | | |
| Compute size | | | |
| Object storage bucket(s) | | | |
| Orchestrator deployment | | | |
| Access | all engineers | + approvers | pipeline SP + on-call + consumers |
| Network | | | locked / private |
| Test data | synthetic / masked sample | full masked copy | real |

## Config layering (lowest -> highest precedence)

1. **Defaults** - `config/defaults.yml` in the repo (safe everywhere).
2. **Per-env overlay** - `config/<env>.yml` (region, sizes, retention, cadence).
3. **IaC outputs** - Terraform writes resource names/ARNs the pipeline needs
   (`config/<env>.generated.yml` or SSM/param store).
4. **Secrets** - resolved at runtime by reference (`env://`, `vault://`,
   `secret-scope://`), never in any file.

No code differs between envs. `dbt --target <env>` + `<env>.tfvars` +
`config/<env>.yml` are the only knobs.

## Promotion

The exact git SHA + dbt `manifest.json` move dev -> test -> prod unchanged
(`cicd-plan.md`). A release is a tag; a rollback is re-deploying an earlier tag.

## Drift detection

- Scheduled `terraform plan` per env (cadence from `deployment-and-iac.md` s.7);
  a non-empty plan alerts + opens an issue.
- `dbt source freshness` + a canary `dbt build` post-deploy confirm health.

## Config keys inventory

| Key | Type | dev | test | prod | Consumed by |
|-----|------|-----|------|------|-------------|
| `warehouse.database` | string | | | | dbt, loader |
| `storage.landing_uri` | string | | | | landing writer |
| `schedule.<pipeline>` | cron | | | | orchestrator |
| `dq.fail_threshold_pct` | number | | | | dbt tests |
| `recon.tolerance_pct` | number | | | | reconciliation |
| ... | | | | | |

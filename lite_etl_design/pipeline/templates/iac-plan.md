# IaC plan

> Phase 4 deliverable. The concrete Terraform (or equivalent) layout to build,
> derived from `design/deployment-and-iac.md`. This file is the build order and
> resource inventory; the design file holds the rationale.

- **Tool & version:** Terraform / OpenTofu / Pulumi / ...
- **Providers (pinned):**
- **Repo path:** `infra/`

## Module tree

```
infra/
  modules/
    <warehouse>/     # catalogs/dbs, schemas, roles/grants, compute, (PII policies)
    storage/         # buckets / external locations, lifecycle, KMS
    orchestrator/    # the tool from 07 (agent / cluster / service)
    observability/   # dashboards, alarms, alert routes
    ci/              # OIDC role(s), runner permissions
  envs/
    dev/   backend.tf  main.tf  dev.tfvars
    test/  ...
    prod/  ...
```

## Resource inventory (per module)

| Module | Key resources | From design ref |
|--------|---------------|-----------------|
| `<warehouse>` | catalog/db, schemas (`raw/bronze`, `staging/silver`, `curated/gold`, restricted), service principal, grants | deployment-and-iac s.1-2 |
| `storage` | landing + lakehouse + tfstate buckets, KMS keys, external locations, lifecycle rules | deployment-and-iac s.1 |
| `orchestrator` | compute / agent / service, task role, networking | 07; deployment-and-iac s.2 |
| `observability` | alarms (cost, freshness, SLA), SNS/PagerDuty/Slack wiring | 09 |
| `ci` | OIDC provider + role per env, least-privilege policy | deployment-and-iac s.4; 08 |

## State backend bootstrap

1. Create the state bucket + lock table **once**, out-of-band or with a
   `bootstrap/` mini-config (no backend).
2. `backend.tf` per env points at `s3://<...>-tfstate/<env>` (+ DynamoDB lock).
3. One state file per env (dir-per-env) / workspaces - match the design.

## Apply order

1. `bootstrap` (state backend) - once per account.
2. `ci` (OIDC) - so pipelines can assume roles.
3. `storage` -> `<warehouse>` -> `orchestrator` -> `observability`.
4. Then Phase 3's `dbt build` creates tables inside the provisioned schemas.

## Per-env variables

| Variable | dev | test | prod |
|----------|-----|------|------|
| region / account | | | |
| compute size | | | |
| retention days | | | |
| alert severity | | | |

## What IaC does NOT manage

(from `deployment-and-iac.md` - dbt objects, secret values, orchestrator DAG
definitions, break-glass grants). Restate here so reviewers don't add them.

## Skeleton files to scaffold

`infra/modules/*/{main.tf,variables.tf,outputs.tf}` and
`infra/envs/*/{backend.tf,main.tf,<env>.tfvars}` - resource blocks named and
wired, variables declared, **values left as `TODO` / `var.` references**. No real
account ids, ARNs, or hostnames.

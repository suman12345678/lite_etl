# Security review - Northwind Commerce (DEMO)

> Phase 5 deliverable. A checklist walk of `requirements/08-security-and-compliance.md`
> against the built pipeline + scaffold. **Input to** an org security review, not
> a substitute for one.

- **Project:** Northwind Commerce - Unified Retail Analytics Harness
- **Reviewer(s):** _(TODO - Analytics Eng lead + Security)_
- **Date:** 2026-09-09 (draft)
- **Baseline:** `requirements/08`, `requirements/06`, `design/deployment-and-iac.md`,
  `pipeline/`, `build/repo/` (Phase 3 + Phase 4 scaffold - stubs + `TODO`s)

## Checklist

| Area | Check | Status | Finding / evidence |
|------|-------|--------|--------------------|
| Secrets | no secret values in repo, fixtures, config, logs, IaC | **PASS** | scan of `pipeline/**` + `build/repo/config/*.yml` clean; `config/*.yml` use `secret-scope://northwind/<env>/...` refs; `.env.example` is a template; `structlog` JSON not yet verified to redact - **note** |
| Secrets | refs resolve via secret manager; rotation documented | **PARTIAL** | `08` documents rotation (Shopify quarterly, SFDC JWT yearly, DB 90d, salt never except RTBF). Resolver `extractors/common/secrets.py` is a stub; **the Databricks secret scopes + ACLs are not in IaC** -> **F2** |
| Secrets | CI uses OIDC / short-lived creds, not stored cloud keys | **PASS** | all 4 workflows use `aws-actions/configure-aws-credentials` + `permissions: id-token: write` + `role-to-assume: arn:...:role/northwind-<env>-ci`; Databricks/Dagster tokens are per-env GitHub Environment secrets |
| Least privilege | pipeline SP writes only its schemas, reads only its sources | **GAP** | `infra/modules/warehouse/main.tf` grants `USE_CATALOG, USE_SCHEMA, CREATE_SCHEMA, MODIFY, SELECT` on the **whole** `northwind_<env>` catalog -> **F3** |
| Least privilege | CI role scoped per env; no `*` policies | **GAP** | `infra/modules/ci/main.tf` `aws_iam_role_policy` body is `Statement = []` (placeholder) + `# TODO least-privilege` -> **F4** |
| PII | classification matches `08`; hashing at the stated point | **PASS (design)** | `08` table -> `silver` hashes email/phone `sha256(salt‖lower(trim()))`, `gold` carries `email_hash` + age band + postcode district, real values only in `gold_pii`; ADR-006; `dbt/macros/surrogate_key.sql` present. Implementation is a stub - **note** |
| PII | restricted zone has row/column policy + named reader group | **GAP** | `northwind_pii_readers` group + a `gold_pii` schema grant exist in `warehouse/main.tf`, but the **UC row filter (marketable-consent) + column mask are `TODO` comments**, not resources -> **F1** |
| PII | PII-leak test present and passing | **PARTIAL** | `build/repo/dbt/tests/assert_no_pii_in_gold.sql` exists (tag `recon`, severity error); it is a stub, not yet passing against real models; value-level sampling unconfirmed (`dq-behaviour-matrix.md` DQ08) |
| PII | right-to-be-forgotten procedure exists and is tested | **GAP** | `08` specifies crypto-shred (drop per-subject salt) + `gold_pii` row delete + inbound file delete + `dim_customer` tombstone (`is_erased`), 30-day SLA, backups honour next cycle. **No script, no runbook section, no drill** -> **F7** |
| Encryption | at rest: landing, target, state, backups - KMS per `08` | **PARTIAL** | `bootstrap` + `storage` modules create per-env SSE-KMS CMKs and set `aws_s3_bucket_server_side_encryption_configuration` on every bucket; Delta inherits. **DynamoDB lock table + ECS task ephemeral storage not explicitly encrypted** -> **F9**. Weekly `eu-west-2` deep clone (`09`) - encryption of the clone target not specified -> **F9** |
| Encryption | in transit: TLS version, mTLS where required | **PASS (design)** | `08` TLS 1.2+ everywhere; JDBC-over-TLS to Postgres is extractor config (`extractors/config/oltp.yml`, `TODO`); AWS + Databricks APIs HTTPS by default - **note** confirm `sslmode=require` in the OLTP config |
| Network | prod isolation (private VPC, no public ingress) as `08` | **GAP** | `08`/`09`: prd = customer-managed VPC, S3 gateway endpoint, no public ingress, Postgres over VPC peering. `infra/modules/orchestrator/main.tf` security group egress is `0.0.0.0/0` with `# TODO tighten`; `vpc_id` / private-subnet lookups are `TODO` -> **F5** |
| Access | raw vs curated read access matches `08`; audited | **PARTIAL** | design matches `08` (`bronze` = Platform + SP; `silver` = Analytics Eng; `gold` = Finance/Marketing/Merch with column masks on commercial fields; `gold_pii` = 5 named readers, audited). Column masks on `margin/cost/wholesale price` are **not** in the scaffold -> folded into **F1/F3** |
| Audit | run manifests, `_recon` reports, deploy logs retained per `06`/`08` | **PARTIAL** | `observability-wiring.md` sets `_recon` 5y / run logs 13mo; **only the inbound bucket has a lifecycle rule** and its value (30/90d) contradicts `08` (`bronze` 60d) -> **F6** |
| Supply chain | dependency scan clean; pinned versions; lockfiles committed | **GAP** | `pyproject.toml` uses `>=` ranges; `uv.lock` is git-ignored (not committed); `pr.yml` `pip-audit` is `|| true` (non-blocking); no `checkov`/`tfsec` yet -> **F8** |
| IaC | `checkov`/`tfsec` clean on high; no public buckets, no `0.0.0.0/0` on data ports | **PARTIAL** | all S3 buckets have `aws_s3_bucket_public_access_block` (**PASS**); orchestrator SG egress `0.0.0.0/0` would fail `tfsec` -> **F5**; scan not wired -> **F8** |
| Retention | per-zone retention + deletion jobs per `08` | **GAP** | no deletion job for `gold_pii` (25 months), `silver` snapshots (90d), `bronze` (60d) beyond the one mis-valued inbound rule -> **F6** |
| Compliance | new-SaaS review for Dagster Cloud (`09` tech constraints, Q3) | **OPEN** | `mode = cloud_agent` is the default; `09` says "No new SaaS without security review (Dagster Cloud pending - Q3)". Go-live blocker if `cloud_agent`; `oss_selfhost` avoids it -> tracked in `go-live-checklist.md` |

## Findings

| # | Severity | Finding | Fix | Owner | Status |
|---|----------|---------|-----|-------|--------|
| **F1** | **High** | `gold_pii` UC **row filter (marketable-consent) + column mask** are `TODO` comments, not resources; column masks on `gold` commercial fields (`margin`/`cost`/`wholesale price`) also absent. This is the core UK-GDPR control from `08` + ADR-006. | Implement the row-filter + column-mask UC functions (Terraform, or dbt post-hook + TF `ALTER ... SET ROW FILTER / SET MASK`); populate `northwind_pii_readers`; add `northwind_finance` / `northwind_merch` column grants on commercial fields. Add fixtures to prove a non-reader sees masked/filtered rows. | Data Platform + Analytics Eng | open |
| **F2** | **High** | Databricks **secret scopes + ACLs** are not in any Terraform module (`/validate-config` #5). `08` requires Terraform to create the scopes/ACLs (values stay in Secrets Manager). Without them the `secret-scope://` refs have nothing to resolve and there is no ACL boundary between envs/principals. | Add `databricks_secret_scope` (AWS-SM-backed) + `databricks_secret_acl` (pipeline SP = READ, humans = MANAGE in dev only) to `warehouse/` or a new `secrets/` module; one scope per `northwind/<env>/<system>`. | Data Platform | open |
| **F3** | Medium | Pipeline **service principal** is granted `CREATE_SCHEMA, MODIFY, SELECT` on the entire `northwind_<env>` catalog - it can read `gold_pii` and write anywhere. `08` = least privilege (write own schemas, read only sources). | Replace the catalog-wide grant with per-schema grants: `MODIFY` on `bronze`/`silver`/`gold`/`gold_pii` only as each stage needs; `SELECT` on sources via external-location grant; **no** standing `SELECT` on `gold_pii` for the SP beyond the publish transaction. | Data Platform | open |
| **F4** | Medium | CI role IAM policy is an empty `Statement = []` placeholder; must be least-privilege per env before any `terraform apply`. | Scope each `northwind-<env>-ci` role to: the env's tfstate bucket + lock table, the resource types its modules manage, `dbt` on the env's Databricks workspace, and the ECS deploy for the agent. No `Resource: "*"`. Add `tfsec`/`checkov` to catch regressions. | Data Platform | open |
| **F5** | Medium | `orchestrator` security-group egress is `0.0.0.0/0`; prd network isolation (`08`/`09`: customer-managed VPC, no public ingress, S3 gateway endpoint, Postgres via peering) is unverified in the scaffold. | Restrict egress to the Databricks control-plane CIDRs, Dagster Cloud (if `cloud_agent`), the S3 gateway-endpoint prefix list, and Secrets Manager; pin prd module inputs to private subnets only; assert no IGW route in prd. | Data Platform | open |
| **F6** | Medium | Retention/lifecycle does not match `08`: only the inbound bucket has a rule and its value (30d dev / 90d prd) contradicts `08` (`bronze` 60d); no deletion for `gold_pii` (25 months), `silver` snapshots (90d), `_recon` (5y keep), logs (13mo). | Set S3 lifecycle + Delta `VACUUM`/retention per the `08` retention table per zone; add a scheduled `gold_pii` 25-month row-deletion job; keep `_recon` 5y / logs 13mo explicitly. | Data Platform + Analytics Eng | open |
| **F7** | Medium | **Right-to-be-forgotten** has no implementation or drill. `08`: crypto-shred (drop per-subject salt), delete `gold_pii` rows + inbound files, tombstone `dim_customer` (`is_erased`, attrs nulled, `customer_sk` kept), 30-day SLA, backups/deep-clones honour on next cycle. | Add `scripts/rtbf.py` + a `runbook.md` RTBF section + a deep-clone propagation step; add the **RTBF drill** to `go-live-checklist.md` (verify a shredded subject is unrecoverable and facts still balance). | Analytics Eng + DPO | open |
| **F8** | Low-Med | Supply chain: `>=` version ranges, `uv.lock` not committed, `pip-audit` non-blocking, no IaC scan. | Pin exact versions, commit `uv.lock` (un-ignore it), flip `pip-audit` to fail-on-critical, add `checkov`+`tfsec` to `pr.yml` (planned in `ci-gates.md`). | Data Eng | open |
| **F9** | Low | DynamoDB lock table and ECS task ephemeral storage not explicitly encrypted; deep-clone target (`eu-west-2`) encryption unspecified. | `server_side_encryption { enabled = true }` on `aws_dynamodb_table.tf_lock`; encrypted volume on the Dagster task def; SSE-KMS on the `eu-west-2` clone bucket. | Data Platform | open |

**Positives recorded:** OIDC-only CI (no stored cloud keys); `aws_s3_bucket_public_access_block`
on every bucket; per-env SSE-KMS CMKs; `gold_pii` same-catalog approach
DPO-approved (Q5); secret scan clean; PII split + leak test designed in;
promotion moves a fixed SHA + manifest (no per-env rebuild).

## Sign-off

- [ ] All **High** findings (F1, F2) closed; **Medium** findings closed or
      accepted with written rationale by the data owner.
- [ ] Dagster Cloud new-SaaS review complete **or** `mode = oss_selfhost` chosen
      (`09` tech constraint / Q3).
- [ ] RTBF drill passed (F7).
- [ ] `checkov` + `tfsec` clean on High against `infra/`.
- [ ] Data owner + Security reviewer sign-off recorded.

Signed: ______________________  Date: __________

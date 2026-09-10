# Security review

> Phase 5 deliverable. A checklist walk of `requirements/08-security-and-compliance.md`
> against the built pipeline, with findings and a sign-off. Not a substitute for
> an org security review - the input to one.

- **Project:**  - **Reviewer(s):**  - **Date:**
- **Baseline:** `requirements/08`, `design/deployment-and-iac.md`,
  `pipeline/`, `build/repo/`

## Checklist

| Area | Check | Status | Finding / evidence |
|------|-------|--------|--------------------|
| Secrets | no secret values in repo, fixtures, config, logs, IaC | | |
| Secrets | all refs resolve via env / vault / secret manager; rotation documented | | |
| Secrets | CI uses OIDC / short-lived creds, not stored cloud keys | | |
| Least privilege | pipeline service principal can write only its schemas, read only its sources | | |
| Least privilege | CI role scoped per env; no `*` policies | | |
| PII | classification matches `08`; masking / hashing / tokenisation applied at the stated point | | |
| PII | restricted zone (`*_SENSITIVE` / `gold_pii`) has row/column policy + a named reader group | | |
| PII | PII-leak test present and passing; no raw PII in non-restricted `gold` | | |
| PII | right-to-be-forgotten procedure exists and is tested (drill) | | |
| Encryption | at rest: landing, target, state store, backups - KMS keys per `08` | | |
| Encryption | in transit: TLS version, mTLS where required | | |
| Network | prod isolation (private link / VPC / no public ingress) as `08` requires | | |
| Access | raw vs curated read access matches `08`; audited | | |
| Audit | run manifests, reconciliation reports, deploy logs retained per `06`/`08` | | |
| Supply chain | dependency scan clean; pinned versions; lockfiles committed | | |
| IaC | `checkov`/`tfsec` clean on high; no public buckets, no `0.0.0.0/0` on data ports | | |
| Retention | per-zone retention + deletion jobs configured per `08` | | |

## Findings

| # | Severity | Finding | Fix | Owner | Status |
|---|----------|---------|-----|-------|--------|
| | | | | | |

## Sign-off

- [ ] All high/critical findings closed or accepted with rationale.
- [ ] Data owner + security reviewer sign-off recorded.
- Signed: ______________________  Date: __________

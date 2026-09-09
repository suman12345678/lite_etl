# 08 - Security & compliance

> DEMO - fictional. GDPR + SOX + BCBS 239.

## Sensitive data

- **Classes present:** PII (customer master), PCI-adjacent (card PAN),
  commercially sensitive (balances, GL)
- **Regulatory regime:** GDPR, SOX, BCBS 239; internal data-classification policy

| Field / entity | Class | Treatment | Applies where |
|----------------|-------|-----------|---------------|
| Card PAN (`card_transactions`) | PCI | **reduced to last 4 at landing**; full PAN never persisted (dropped in the ETL parser, in memory only) | everywhere |
| `customer_master.full_name` | PII | **FPE tokenised** before landing | RAW/STAGING/CURATED; real value only in `CURATED_SENSITIVE` |
| `customer_master.date_of_birth` | PII | tokenised (date-preserving) before landing | as above |
| `customer_master.national_id` | PII (special category in some countries) | tokenised before landing | as above |
| `customer_master.address` | PII | tokenised (line-level) before landing | as above |
| `DIM_CUSTOMER` non-sensitive attrs (country, segment, risk_rating) | internal | none | CURATED |
| account balances, GL amounts | confidential | RBAC only | CURATED |

- **`CURATED_SENSITIVE`:** holds the real name / DOB / national id / address,
  joined by `customer_sk`. Snowflake **row-access + masking policies**; only a
  named group (KYC/AML analysts, approved by DPO) can read. All access logged.

## Secret management

- **Mechanism:** AWS Secrets Manager (DB creds, GCP SA key) + HashiCorp Vault
  (SFTP private key, FPE tokenisation keys)
- **Reference scheme in config:** `awssm://meridian/<env>/<name>` and
  `vault://secret/meridian/<env>/<name>#<field>` - resolved at run time, never
  written to logs, config, or the repo
- **Rotation:** DB creds 90 days (automatic); SFTP key annually; tokenisation
  keys are long-lived, escrowed, and crypto-shred is the deletion mechanism

## Encryption

- **In transit:** TLS 1.2+ everywhere; SFTP over SSH with pinned host key;
  Snowflake and AWS APIs via the egress proxy
- **At rest:** S3 SSE-KMS (per-env CMK), Snowflake encryption (Tri-Secret Secure
  with a customer-managed key in prod), MWAA + CloudWatch KMS-encrypted

## Access control

- Raw/landing S3: Risk Data engineers + pipeline role only
- `STAGING`: Risk Data team
- `CURATED`: Risk Data (write), Regulatory Reporting + Finance (read via roles)
- `CURATED_SENSITIVE`: named analysts, DPO-approved, row-access policy, audited
- Pipeline runs under a **least-privilege** role per source (read only what it
  needs); no shared "admin" service account

## Retention & deletion

- **Retention:** RAW/landing 90 days; `STAGING` 30 days; `CURATED` and all audit
  metadata 7 years; then automated purge
- **Right-to-be-forgotten:** a GDPR erasure request is honoured by
  **crypto-shredding** that customer's tokenisation key mapping (renders
  tokenised values irreversible) + deleting the `CURATED_SENSITIVE` row; curated
  aggregates retain the tokenised `customer_sk` only. SLA: 30 days. Process
  owned by DPO, executed by Risk Data. (DPO sign-off on the UAT test of this -
  Q4, resolved: approved 2026-09-03.)

# 08 - Security & compliance

> DEMO - fictional. Version 1.1 (Q5 folded in).

## Sensitive data

- **Classes present:** PII (customer identity + contact + DOB + address);
  commercially sensitive (margin, cost, wholesale pricing). No PCI (Shopify /
  POS tokenise cards upstream; we never receive PANs). No PHI.
- **Regulatory regime:** UK GDPR (+ EU GDPR for EU customers).

| Field / entity | Class | Treatment | Applies where |
|----------------|-------|-----------|---------------|
| customer email | PII | `sha256(salt \|\| lower(trim(email)))` for joins/segments; real value only in `gold_pii` | hash in `silver`+`gold`; real in `gold_pii` |
| customer phone | PII | hash (same scheme) in `gold`; real in `gold_pii` | as above |
| customer name | PII | not carried into `gold`; real in `gold_pii` only | `gold_pii` |
| shipping / billing address | PII | city + country + postcode-district only in `gold`; full address in `gold_pii` | split |
| date of birth | PII | age band (`18-24`, ...) in `gold`; real DOB in `gold_pii` | split |
| margin / cost / wholesale price | commercial | column-level grant; `northwind_finance` + `northwind_merch` only | `gold.fct_order`, `dim_product` |
| `bronze.*` raw | PII in the clear briefly | access limited to Data Platform + pipeline SP; 60-day retention; SSE-KMS | `bronze` |

- **`gold_pii` isolation (Q5 - resolved):** stays in the same catalog as `gold`,
  governed by a Unity Catalog **row filter** + **column mask** and a dedicated
  `northwind_pii_readers` group (DPO-approved). No separate workspace.

## Secret management

- **Mechanism:** Databricks **secret scopes** backed by AWS Secrets Manager;
  Terraform creates the scopes/ACLs (not the values). GitHub Actions uses OIDC
  federation to an AWS role - no long-lived cloud keys in CI.
- **Reference scheme:** `secret-scope://northwind/<env>/<system>#<field>` in
  config; `awssm://northwind/<env>/<system>` behind it.
- **Rotation:** Shopify token quarterly; Salesforce JWT key yearly; DB creds
  90 days; hashing salt **never rotated** except for RTBF crypto-shred.

## Encryption

- **In transit:** TLS 1.2+ everywhere; JDBC to Postgres over TLS; S3 + Databricks
  APIs HTTPS.
- **At rest:** S3 buckets (inbound, lakehouse, state) SSE-KMS with a
  customer-managed key per env; Delta inherits; Secrets Manager KMS; EBS on the
  Dagster ECS task encrypted.

## Access control

- **Raw (`bronze`):** Data Platform + the pipeline service principal only.
- **`silver`:** Analytics Eng.
- **`gold`:** Finance, Marketing, Merchandising (read) via UC grants; column
  masks on commercial fields.
- **`gold_pii`:** `northwind_pii_readers` (5 named people) only; every query
  audited; UC row filter enforces marketable-consent scope for Marketing use.
- **Pipeline identity:** one Databricks **service principal** per env, least
  privilege (write its own schemas, read sources); no personal tokens in
  automation.

## Retention & deletion

- **Retention:** `bronze` 60 days; `silver` snapshots 90 days; `gold` 5 years
  (Finance); `gold_pii` 25 months; `_recon` reports 5 years; run logs 13 months.
- **Right-to-be-forgotten:** on a verified request - crypto-shred the subject
  (drop their per-subject salt so the hash can never be re-derived), delete rows
  from `gold_pii` and inbound files, tombstone `dim_customer`
  (`is_erased = true`, attrs nulled, `customer_sk` kept for fact integrity).
  SLA: 30 days. Backups/deep-clones honour the same list on their next cycle.

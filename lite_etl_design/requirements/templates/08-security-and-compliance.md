# 08 - Security & compliance

## Sensitive data

- **Classes present:** PII / PHI / PCI / commercially sensitive / none
- **Regulatory regime:** GDPR / HIPAA / SOX / CCPA / internal only / other

| Field / entity | Class | Treatment (mask / hash / tokenise / encrypt / drop / row-filter) | Applies where (raw / curated / both) |
|----------------|-------|------------------------------------------------------------------|--------------------------------------|
| | | | |

## Secret management

- **Mechanism:** env vars / HashiCorp Vault / AWS Secrets Manager /
  GCP Secret Manager / Azure Key Vault / key files
- **Reference scheme:** e.g. `env://VAR`, `vault://path#field`, `awssm://name`
- **Rotation expectations:**

## Encryption

- **In transit:** required standard (TLS version, mTLS?)
- **At rest:** landing zone, target, state store - required standard / KMS keys

## Access control

- Who may read raw vs cleansed vs curated
- Row-level / column-level restrictions
- Service-account model for the pipeline itself (least privilege)

## Retention & deletion

- **Data retention period** per zone
- **Right-to-be-forgotten / deletion requests:** how honoured, SLA

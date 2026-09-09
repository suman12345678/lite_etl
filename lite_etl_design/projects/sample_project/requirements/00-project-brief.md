# 00 - Project brief

> Phase 1 deliverable. Produced by the `gather-etl-requirements` skill on
> 2026-09-03 from `intake/meridian-trust-rfp-extract.md` plus the interview.
> DEMO - fictional client.

- **Project name:** Meridian Trust - Regulatory & Risk Data Harness
- **Date / version:** 2026-09-03 / v1.1 (v1.0 at interview, v1.1 after `/finalize-requirements`)
- **Prepared with:** Head of Risk Data (sponsor), Regulatory Reporting lead, Finance systems lead, Data Platform engineer, DPO (async)

## Business goal

Replace the manual, spreadsheet-based assembly of regulatory and risk data with
a governed pipeline that lands source data reliably, enforces data-quality and
reconciliation controls, and publishes a trusted curated layer. The curated
layer feeds (a) the existing Basel III / BCBS 239 regulatory extract at 07:00
CET and (b) Finance's month-end close. Target outcome: month-end close down from
9 working days to 4, zero re-filed submissions caused by reconciliation breaks.

## Stakeholders

| Role | Name / team | Interest |
|------|-------------|----------|
| Sponsor | Head of Risk Data | on-time, audit-defensible regulatory data |
| Data owner (curated) | Risk Data team | owns CURATED schema and its contracts |
| Data owner (GL feed) | Finance Systems | GL balances correctness, tie-out |
| Consumer | Regulatory Reporting | 07:00 CET extract, BCBS 239 field completeness |
| Consumer | Finance close team | reconciled sub-ledger vs GL |
| Governance | DPO / Legal | GDPR treatment of customer master |
| Ops | Data Platform / Risk Data on-call | run health, SLA |

## Success criteria

- CURATED layer for a business date is complete, reconciled (PASS), and signed
  off by **06:00 CET**, every business day, for 20 consecutive days before
  go-live sign-off.
- 100% of BCBS 239 mandatory fields (final list - see Q1) populated or explicitly
  flagged, with column-level lineage available for every one.
- GL tie-out (debits == credits per journal; opening + movements == closing per
  account/day) passes with zero manual journals for 3 consecutive month-ends.
- A re-run of any business date produces identical curated output (idempotent) -
  no double counting.
- Any published number can be traced to source system, extract run id, and
  transformation version within 2 minutes.

## Scope

**In scope:**

- Extraction from 5 sources: core banking (Oracle), card transactions (SFTP
  file), GL balances (BigQuery), FX rates (REST), customer master (SQL Server).
- Landing zone, transformation to a curated dimensional model in Snowflake.
- Data-quality rules, reconciliation controls with a hard publish gate.
- Column-level lineage and catalog registration.
- Orchestration, alerting, backfill, dev/UAT/prod separation.

**Out of scope:**

- Real-time / intraday processing (T+1 batch only).
- The regulatory calculation engine (fed by, not built here).
- Source system changes or decommissioning.
- BI dashboards on top of CURATED (consumer's own concern).

## Constraints

- **Timeline / milestones:** design sign-off end of Sep 2026; first source
  (core banking) landing in UAT end of Oct; full go-live target Q1 2027.
- **Team skills / preferred stack:** Python + SQL strong; 2 engineers know dbt
  and Airflow. Prefer managed services over self-hosted.
- **Budget / cost ceiling:** combined Snowflake + AWS run cost < EUR 8,000 / month.
- **Mandated platform:** Snowflake (contract signed); AWS is the cloud;
  prod is an isolated AWS account.

## Assumptions

- Card processor cannot yet provide intraday files; daily file is the contract
  (revisit - Q3).
- Finance's BigQuery GL replica is authoritative and stable; we do not read SAP
  directly.
- Reporting currency is EUR for all curated outputs.
- Source read replicas / exports are available in all three environments (Q5).

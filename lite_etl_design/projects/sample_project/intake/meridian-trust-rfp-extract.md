# Meridian Trust Bank - extract from the RFP / discovery notes

> This is the raw material the client handed over before the interview. It was
> dropped into `intake/` so the `/gather-requirements` interview could read it
> first and only ask about the gaps.
>
> **Fictional - for harness demo purposes only.**

## Background (from the RFP, section 2)

Meridian Trust Bank is a mid-size retail and commercial bank (approx. 1.9M
customers, 2.4M accounts, ~40 branches). The Risk & Regulatory Reporting
function currently assembles Basel III liquidity metrics, BCBS 239 risk data,
and the AML transaction-monitoring feed by hand from three system exports plus
spreadsheets. Month-end close takes 9 working days and the last two regulatory
submissions were re-filed due to reconciliation breaks.

They want a governed "data harness" that lands source data reliably, applies
data-quality and reconciliation controls, and produces a trusted curated layer
that both the regulatory extract and the finance team can rely on.

## What they told us in discovery (unstructured)

- Core banking is **Oracle** (vendor platform, read replica available). Account
  and balance data. They think ~500k rows change per day. There is a
  `LAST_MOD_TS` column.
- Card transactions come from the card processor as a **daily pipe-delimited
  file over SFTP**, landing around 01:30. "Millions of rows." Amounts are in
  minor units, right-justified. Occasionally the file is split into two parts.
- The finance GL lives in **SAP**, but Finance already replicates GL balances
  into **BigQuery** every night and is happy for us to read from there.
- FX rates - they currently copy the ECB daily rates into a spreadsheet. There
  is a public REST endpoint.
- Customer master (name, address, DOB, national ID) is in a **SQL Server** CRM.
  This is the most sensitive data. Legal has flagged GDPR.
- Target should be **Snowflake** - they have just signed a contract.
- Reporting currency is **EUR**. Some accounts are USD and GBP.
- Regulatory extract runs at **07:00 CET**; curated data must be ready and signed
  off before then.
- They are a **SOX**-regulated group and must satisfy **BCBS 239** (risk data
  aggregation) and **GDPR**.
- Card PANs must never be stored in full. Finance only ever needs last 4 digits.
- The team is comfortable with **Python and SQL**; two engineers have used
  **dbt** and **Airflow**.
- Budget guidance for run cost: "keep Snowflake + AWS under 8k a month".
- They want dev / UAT / prod separated properly - prod is a locked-down AWS
  account.

## Known pain points they explicitly listed

1. GL never ties out to the sub-ledgers without manual journals.
2. Card file sometimes arrives late or in two parts; downstream breaks.
3. No lineage - when a number is questioned, nobody can show where it came from.
4. Re-running a day's load currently double-counts.

## Out of scope (client stated)

- Real-time / intraday processing (T+1 batch is fine for now).
- The regulatory calculation engine itself (they keep their existing tool - we
  just feed it).
- Decommissioning the source systems.

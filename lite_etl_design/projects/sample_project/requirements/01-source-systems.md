# 01 - Source systems

> DEMO - fictional. 5 sources. Secrets are named by location only.

## Summary

| Slug | Type | Mode | Volume/day | Cadence | Owner |
|------|------|------|-----------|---------|-------|
| `core_banking_accounts` | sql (Oracle) | incremental | ~500k changed rows | daily 02:00 CET | Core Banking Ops |
| `card_transactions` | csv (SFTP drop) | file-arrival | ~8M rows | daily, file ~01:30 CET | Cards / processor |
| `general_ledger` | bigquery | full snapshot | ~220k rows | daily ~00:45 CET | Finance Systems |
| `fx_rates` | rest_api | full (small) | ~170 rows | daily ~16:00 CET (ECB) | Risk Data |
| `customer_master` | sql (SQL Server) | incremental | ~30k changed rows | daily 02:00 CET | CRM / Legal (PII) |

---

## Source: `core_banking_accounts`

- **Subject area / domain:** deposits / accounts
- **System of record:** Oracle core banking (vendor platform), read replica
- **Type:** `sql` (engine: Oracle 19c)
- **How we reach it:** host `orax-replica.meridian.internal:1521`, service
  `COREREP`, schema `CB`, tables `CB.ACCOUNT`, `CB.ACCOUNT_BALANCE`, `CB.PRODUCT`
- **Auth method (reference, not value):** service account, password in AWS
  Secrets Manager `meridian/uat/core_banking_ro` (per-env)
- **Objects to extract:** `SELECT ... FROM CB.ACCOUNT a JOIN CB.ACCOUNT_BALANCE b
  ... WHERE a.LAST_MOD_TS > :watermark OR b.LAST_MOD_TS > :watermark`
- **Extract mode:** incremental
- **Watermark column:** `LAST_MOD_TS` (TIMESTAMP, stored UTC in DB, confirmed)
- **Expected volume:** ~500k changed rows/day; full seed ~2.4M rows / ~1.1 GB
- **Source freshness:** replica lag < 5 min; safe to read from 02:00
- **Format & encoding:** n/a (DB). Land as Parquet, UTF-8, timestamps to UTC
- **Known quirks:** `CCY` sometimes lower-case; closed accounts keep balance
  rows; a handful of test accounts with `PRODUCT_CODE = 'ZZZ'` to be filtered
- **Sample / data dictionary available?** yes - Oracle DDL export in `intake/` (pending, Q1)
- **Downstream use:** `DIM_ACCOUNT` (SCD2), `FACT_ACCOUNT_BALANCE_DAILY`

## Source: `card_transactions`

- **Subject area / domain:** cards
- **System of record:** external card processor
- **Type:** `csv` over SFTP
- **How we reach it:** SFTP `sftp.cardproc.example.com`, path
  `/outbound/meridian/CARDTXN_YYYYMMDD*.psv`
- **Auth method:** SSH key pair; private key in Vault
  `secret/meridian/<env>/sftp_cardproc#private_key`; host key pinned
- **Objects to extract:** all files matching `CARDTXN_<business_date>*.psv`
  (may be `..._01.psv` and `..._02.psv`)
- **Extract mode:** file-arrival (sensor waits until a `.done` marker or a
  timeout; both parts required if present)
- **Watermark column:** n/a - business date is in the filename
- **Expected volume:** ~8M rows/day, ~1.6 GB across parts
- **Source freshness:** file targeted for 01:30 CET; SLA breach if not complete by 03:30
- **Format & encoding:** pipe-delimited (`|`), header row present, Windows-1252,
  `CRLF`; amounts in **minor units, right-justified, zero-padded width 12**;
  `POST_DATE` as `YYYYMMDD`
- **Known quirks:** split files; occasional trailing summary line
  (`TOTAL|<count>|<amount>`) that must be dropped and used for reconciliation;
  PAN present in full in the raw file - must be reduced to last 4 at landing
- **Downstream use:** `FACT_CARD_TXN`
- **See also:** `04-data-quality.md`, `05-reconciliation.md`, `08-security-and-compliance.md`

## Source: `general_ledger`

- **Subject area / domain:** finance / GL
- **System of record:** SAP, replicated by Finance into BigQuery
- **Type:** `bigquery`
- **How we reach it:** project `meridian-finance-<env>`, dataset `gl_replica`,
  tables `gl_balance_daily`, `gl_journal_header`, `chart_of_accounts`
- **Auth method:** GCP service account key in AWS Secrets Manager
  `meridian/<env>/bq_gl_reader`; least-privilege (dataset viewer)
- **Objects to extract:** full daily snapshot of `gl_balance_daily` for the
  business date + `gl_journal_header` for the date + `chart_of_accounts` (full)
- **Extract mode:** full snapshot per business date
- **Watermark column:** n/a (full snapshot; `business_date` predicate)
- **Expected volume:** ~200k balance rows + ~20k journal rows/day
- **Source freshness:** replica completes ~00:45 CET; read after 01:00
- **Format & encoding:** BigQuery native; land as Parquet
- **Known quirks:** amounts already in EUR; `posting_date` vs `business_date` can
  differ for back-dated journals; some accounts have both DR and CR lines
- **Downstream use:** `FACT_GL_BALANCE`, GL tie-out reconciliation

## Source: `fx_rates`

- **Subject area / domain:** reference data
- **System of record:** European Central Bank daily reference rates (public)
- **Type:** `rest_api`
- **How we reach it:** `GET https://data-api.ecb.example/eurofxref/daily` (XML/JSON)
- **Auth method:** none (public); still routed through the egress proxy
- **Objects to extract:** all currency/rate pairs for the published date
- **Extract mode:** full (small reference set)
- **Watermark column:** publication date in the payload
- **Expected volume:** ~170 rows/day
- **Source freshness:** published ~16:00 CET on TARGET business days; no
  publication on ECB holidays - carry forward last known rate (see 03)
- **Format & encoding:** JSON; rates as decimal strings; base currency EUR
- **Known quirks:** missing days (holidays); occasional currency added/removed
- **Downstream use:** currency conversion in `03-transformations.md`;
  `DIM_FX_RATE`

## Source: `customer_master`

- **Subject area / domain:** party / customer (PII)
- **System of record:** SQL Server CRM
- **Type:** `sql` (engine: SQL Server 2019)
- **How we reach it:** host `crm-sql-replica.meridian.internal`, database `CRM`,
  tables `dbo.Customer`, `dbo.CustomerAddress`, `dbo.CustomerIdentification`
- **Auth method:** service account, password in Vault
  `secret/meridian/<env>/crm_ro#password`
- **Objects to extract:** `WHERE ModifiedUtc > :watermark`
- **Extract mode:** incremental
- **Watermark column:** `ModifiedUtc` (datetime2, UTC)
- **Expected volume:** ~30k changed rows/day; full seed ~1.9M
- **Source freshness:** replica lag < 10 min
- **Format & encoding:** land as Parquet, UTF-8
- **Known quirks:** `DateOfBirth` occasionally `1900-01-01` placeholder;
  `NationalId` formats vary by country; free-text address lines
- **PII:** name, DOB, national ID, address - full treatment in
  `08-security-and-compliance.md` (tokenised outside `CURATED_SENSITIVE`)
- **Downstream use:** `DIM_CUSTOMER` (SCD2)

---

## Cross-source notes

- **Shared connection profiles:** one Oracle profile reused if more core-banking
  objects are added later; one SFTP profile.
- **Ordering:** `fx_rates` must land before any currency conversion.
  `core_banking_accounts` + `customer_master` must land and build their dims
  before `card_transactions` and `general_ledger` facts are loaded.

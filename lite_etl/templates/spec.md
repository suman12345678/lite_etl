# Spec — <project>

engine: duckdb | databricks | snowflake      <!-- duckdb = local demo -->
owner: <name>    date: <yyyy-mm-dd>

## Sources
| name | kind | grain | load | quirks |
|------|------|-------|------|--------|
| | postgres / rest / s3-file / warehouse / api | row / event | full / incremental / cdc | e.g. late data, supersede, multi-currency |

## Target
- zones: raw -> staging -> marts        <!-- rename to bronze/silver/gold if you like -->
- model: <dims and facts, one line each, with grain>
- keys: <business key per table>

## Transforms
- <one rule per line: cast/rename, dedupe on X keep latest, currency -> USD at rate_date, drop test rows, ...>

## Rules
<!-- these become repo/rules.yml -->
- quality: <table>.<col> <check>        on_fail: warn | quarantine | fail
- reconcile: <measure> vs <source of truth>   tolerance <n>%   on_fail: block

## Schedule
- cadence: <cron or file-arrival>    deadline: <time>
- backfill: <how a date range is re-run>

## Non-functional
- volume: <rows / size / growth>   latency: <SLA>   cost: <ceiling>
- pii: <none | fields + handling>
- envs: <dev, prod, ...>

## Open questions
- <thing not yet decided>

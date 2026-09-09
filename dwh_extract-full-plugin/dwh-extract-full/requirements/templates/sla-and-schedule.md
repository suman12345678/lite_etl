# SLA & schedule

- **Cadence:**             cron expression (UTC), e.g. `0 5 * * *`
- **Delivery deadline:**   landed + reconciled by <time>
- **Dependencies:**        upstream feeds / reference data that must land first
- **Calendar:**            business days only? holiday calendar?
- **Catch-up policy:**     backfill missed windows? how many?
- **Retry policy:**        attempts, backoff, transient-vs-permanent
- **Escalation:**          who is paged on SLA miss / recon failure
- **Environments:**        which of dev/test/prod this applies to

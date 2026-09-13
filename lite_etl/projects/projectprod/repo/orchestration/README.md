# orchestration/

The cron orchestrator (design.md Decisions: "Orchestrator = cron, two cadences").
One container image, two schedules, both wired two ways:

| cadence | script | crontab.txt | infra (AWS) |
|---------|--------|-------------|--------------|
| daily 02:00 | `run_daily.sh` | `0 2 * * *` | `aws_cloudwatch_event_rule.daily` -> ECS Fargate task `daily` |
| hourly | `run_hourly_land.sh` | `0 * * * *` | `aws_cloudwatch_event_rule.hourly` -> ECS Fargate task `hourly` |
| backfill | `run_backfill.sh <start> <end>` | run manually / via a one-off ECS `RunTask` | n/a (on demand) |

Every script assumes `ENGINE` and this engine's credentials are already in the
environment (see `../README.md`). Nothing in this directory contains a literal
credential, host, or account id.

# DQ behaviour matrix

> Phase 5 deliverable. Every data-quality rule from `requirements/04-data-quality.md`
> crossed with the input scenarios that exercise it, and the routing the pipeline
> must produce. This is the executable spec for the DQ engine / dbt tests.

- **Rules source:** `requirements/04-data-quality.md`
- **Implemented as:** dbt tests / DQ engine (from `design/transformation-design.md` s.6)
- **Routing outcomes:** `pass` | `warn` (load + alert) | `quarantine` (row to
  reject table + reason) | `fail` (abort run, no publish)

## Matrix

| Rule (id / field) | Dimension | Input scenario (fixture) | Expected routing | Threshold effect | Test |
|-------------------|-----------|--------------------------|------------------|------------------|------|
| `<id>` `<field> not null` | completeness | value present | pass | - | `not_null` |
| | | value null, 1 row | quarantine, reason `null_<field>` | counts toward reject rate | singular |
| | | value null, > fail threshold | fail run | reject rate > `<x>%` | threshold test |
| `<id>` `<field> in set` | validity | allowed value | pass | | `accepted_values` |
| | | disallowed value | quarantine, reason `bad_<field>` | | |
| `<id>` key unique | uniqueness | unique keys | pass | | `unique` |
| | | duplicate key | dedupe per rule / quarantine | | |
| `<id>` FK resolves | referential | parent exists | pass | | `relationships` |
| | | parent missing | load with unknown-member `-1` + warn | | |
| `<id>` freshness | timeliness | within window | pass | | `source freshness` |
| | | stale beyond error_after | fail run | | |
| `<id>` range / regex | validity | in range | pass | | `dbt_expectations` |
| | | out of range | quarantine or fail per severity | | |
| PII-leak | security | no raw PII in `gold.*` | pass | | singular, severity error |
| | | raw email present | fail run, block publish | | |

(Add a block per rule in `04`. Every rule must appear with at least a
pass row and a fail/quarantine row.)

## Threshold cases

| Scenario | Reject rate | Expected |
|----------|-------------|----------|
| below warn | < `<warn>%` | run proceeds silently |
| warn band | `<warn>%`..`<fail>%` | run proceeds, alert fires |
| at fail threshold | = `<fail>%` | documented (fail / proceed) |
| above fail | > `<fail>%` | run fails, nothing publishes |

## Reporting assertions

- Each quarantined row lands in `reject__<entity>` with `reason_code`,
  `_run_id`, `_dq_rule`.
- The DQ report / dashboard shows per-rule pass counts and the reject rate for
  the run.

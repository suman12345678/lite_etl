# Design — <project>

## Approach
ELT: land raw -> dbt (<engine>) -> rule checks -> publish.
Orchestrator: <cron | Dagster | Airflow | none>.   Infra: Terraform.

## Components
| component | does | spec ref |
|-----------|------|----------|
| extract/<src> | pull <src> -> raw | Sources |
| dbt | raw -> staging -> marts | Target, Transforms |
| rules | run rules.yml; quarantine rows / block publish | Rules |
| publish | commit marts + _SUCCESS + advance watermark | Target, Schedule |
| infra | catalog/warehouse, storage, roles | Non-functional, envs |
| ci | lint · demo · dbt build · tf validate | envs |
<!-- add/remove rows to match the spec -->

## Data flow
see diagram.md

## Decisions
- <choice> because <spec item>

## Maps to spec
Every row in Sources / Target / Transforms / Rules / Schedule / Non-functional -> a component above.
Gaps: <none | list>

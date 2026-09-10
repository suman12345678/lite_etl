# lite_etl

A small, editable harness for designing an ETL pipeline. Three phases, one folder per pipeline.
Every file here is short on purpose — read it, change it.

## Use

    /etl-spec <name>    1. interview  -> projects/<name>/spec.md
    /etl-design         2. spec       -> design.md + diagram.md
    /etl-build          3. scaffold   -> repo/ with a runnable local demo
    /etl-status         where am I, what's next

## Layout

    templates/          spec.md · design.md · rules.yml   — the shape each phase fills
    .claude/skills/     one skill per phase (+ status)
    .claude/agents/     scaffolder — optional, does the bulk repo/ build
    projects/<name>/    spec.md  design.md  diagram.md  repo/  progress.json

## Model

- **engine**: `duckdb` (local demo) · `databricks` · `snowflake`. dbt for transforms, Terraform for infra.
- **rules** = data quality + reconciliation, all in one file: `repo/rules.yml`.
- Every design component names the spec item it satisfies.
- `/etl-build` produces a repo that actually runs: `make demo` loads data, applies rules, publishes or blocks.

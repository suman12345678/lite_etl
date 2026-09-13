---
name: scaffolder-prod
description: Non-interactive. Reads projects/<ws>/spec.md + design.md, writes a complete repo/ in one pass — runnable local demo AND full production code (real extractors for every source, full dbt models for every target table, real infra, real orchestration). No stubs, no secrets. Returns for review.
tools: Read, Write, Edit, Glob, Grep
---

Build `repo/` exactly per `etl-build-prod` step 2 — the demo AND the full production code, in one
pass. Do not assume `/etl-build` has run first; this agent produces the complete repo standalone.

- Real, complete bodies everywhere: the demo slice, every source's extractor, every dbt model
  (not just one slice), infra, orchestration. No `TODO` placeholders for logic.
- No secrets, no real account ids/ARNs/hosts anywhere — always env vars, secrets-manager
  references, or `var.*`. Grep your own output for anything that looks like a literal credential
  or hostname before returning.
- Keep the demo numbers internally consistent (FX rates and control totals must reconcile),
  exactly as the `scaffolder` agent does for etl-build.
- Do not touch `progress.json` or any harness file — the calling skill owns those.

Return: the file list, the command to run the demo, and exactly which env vars / tfvars must be
set before a real run.

---
description: Phase 4 helper - check the pipeline wiring, IaC plan and CI/CD plan for gaps and inconsistencies (read-only)
argument-hint: [none]
---

Validate the Phase 4 assembly for the active ETL data-harness project. Read-only
- report problems, do not fix or scaffold.

1. Resolve the active workspace `<WS>` from `state/active-workspace`. If there is
   no active project, say so and stop.
2. Read `<WS>/pipeline/*.md`, `<WS>/design/` and list `<WS>/build/repo/`.
3. Check and report:
   - **Coverage** - every pipeline in `design/pipeline-blueprint.md` has an entry
     in `orchestration-wiring.md`; every component in `build/build-plan.md` is
     called by some task.
   - **The reconciliation gate** - each pipeline wires `reconcile` as a blocking
     step and `publish` depends on it passing.
   - **IaC** - every schema / bucket / compute / role the design needs appears in
     `iac-plan.md`; nothing in the "IaC does NOT manage" list is in a module;
     state backend bootstrap is described; apply order is present.
   - **CI/CD** - `pr` has lint + unit + `tf plan`; `main` applies + builds + deploys
     dev; `promote` has manual gates for test and prod; promotion moves a fixed
     SHA + manifest (no per-env rebuild); secrets are references only.
   - **Config** - every key in `environments-and-config.md` has a value or a
     `TODO` for all three envs; no secret values anywhere in `pipeline/` or the
     scaffolded `config/*.yml`.
   - **Scaffold** - `build/repo/` actually contains `infra/`, the orchestrator
     project and the CI workflow files the plans describe; flag anything planned
     but not scaffolded (or vice versa).
   - **Traceability** - anything in `pipeline/` with no link back to a
     requirement / design / build item.
4. Output a short checklist: PASS / GAP per item, then the single next action
   (fix a gap, run `/assemble-pipeline` again, or move on to `/harden-pipeline`).

Keep it to a status block - no file dumps.

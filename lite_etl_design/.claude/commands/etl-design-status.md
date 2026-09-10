---
description: Show where the ETL data-harness design process stands and what to do next
argument-hint: [none]
---

Report the state of the ETL data-harness design.

1. Read `state/active-workspace`. If empty/missing, say "no active project" and
   tell me to run `/etl-new-project <name>`; also list any folders under
   `projects/` that already contain `project.json`.
2. For the active workspace `<WS>`:
   - read `<WS>/project.json` and `<WS>/progress.json`
   - list files present in `<WS>/requirements/`, `<WS>/design/`, `<WS>/build/`
     (incl. whether `<WS>/build/repo/` exists and a rough file count),
     `<WS>/pipeline/`, `<WS>/hardening/`
   - list anything sitting in `<WS>/intake/`
   - read `<WS>/requirements/99-open-questions.md` if it exists and summarise the
     open items
3. Tell me: the active project + its path, the active phase, which of the five
   phases are complete / in progress / not started, what is missing, and the
   single next command to run.

The phase -> command map:
`1_requirements` -> `/gather-requirements` · `2_architecture` -> `/design-architecture`
· `3_build_and_test` -> `/build-components` · `4_pipeline_and_git` ->
`/assemble-pipeline` (then `/validate-config`) · `5_full_testing_and_hardening` ->
`/harden-pipeline`.

Keep it to a short status block - no file dumps.

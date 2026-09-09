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
   - list `<WS>/requirements/` and `<WS>/design/` (files present)
   - list anything sitting in `<WS>/intake/`
   - read `<WS>/requirements/99-open-questions.md` if it exists and summarise the
     open items
3. Tell me: the active project + its path, the active phase, what is complete,
   what is missing, and the single next command to run.

Keep it to a short status block - no file dumps.

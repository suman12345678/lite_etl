---
description: Phase 1 - run the interactive ETL requirements interview and write requirement files
argument-hint: [optional note about the project or what to focus on]
---

Start (or resume) **Phase 1 - Requirements** of the ETL data-harness design.

Invoke the `gather-etl-requirements` skill and follow it exactly:

1. Resolve the active project workspace `<WS>` from `state/active-workspace`.
   If there is no active project, tell me to run `/etl-new-project <name>` and stop.
2. Read `<WS>/progress.json`, everything in `<WS>/intake/`, the harness
   `requirements/question-bank.md`, and the harness `requirements/templates/`.
3. Interview me area by area. Ask about gaps; don't dump the whole question bank.
   Use `AskUserQuestion` for multiple-choice decisions.
4. When coverage is good enough to design against, write one file per area to
   `<WS>/requirements/`, plus `README.md` and `99-open-questions.md`.
5. Update `<WS>/progress.json` and tell me the top open questions.

If I gave a note above, use it to bias where we start: $ARGUMENTS

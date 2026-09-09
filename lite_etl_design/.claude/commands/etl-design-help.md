---
description: Explain this ETL design harness - phases, commands, skills, agents, projects, and where files go
argument-hint: [none]
---

Explain how to use the lite-etl-design harness.

Read `MAP.md`, `README.md`, and `docs/process-overview.md`, then give me a
concise briefing:

- The harness vs a project workspace, and that a project can live in a subfolder
  (`projects/<name>/`) or any other folder on disk.
- The step-by-step process and which steps are built today (1 and 2) vs planned.
- The main-flow commands in order (`/etl-new-project` -> `/gather-requirements`
  -> `/design-architecture`) and the auxiliary helpers
  (`/etl-design-status`, `/finalize-requirements`, `/etl-design-help`).
- The difference between a skill, a subagent, a slash command and the
  SessionStart hook in this harness, and when each runs.
- Where I put inputs (`<workspace>/intake/`) and where deliverables land
  (`<workspace>/requirements/`, `<workspace>/design/`).
- The exact next command for my current state (check `state/active-workspace`
  then `<workspace>/progress.json`).

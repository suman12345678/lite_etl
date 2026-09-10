---
description: Explain this ETL design harness - phases, commands, skills, agents, projects, and where files go
argument-hint: [none]
---

Explain how to use the lite-etl-design harness.

Read `MAP.md`, `README.md`, and `docs/process-overview.md`, then give me a
concise briefing:

- The harness vs a project workspace, and that a project can live in a subfolder
  (`projects/<name>/`) or any other folder on disk.
- The five-step process, all now built:
  1 requirements, 2 architecture, 3 build & test components, 4 pipeline & Git,
  5 full testing & hardening - what each produces and where it lands
  (`<workspace>/requirements|design|build|pipeline|hardening/`).
- The main-flow commands in order (`/etl-new-project` -> `/gather-requirements`
  -> `/design-architecture` -> `/build-components` -> `/assemble-pipeline` ->
  `/harden-pipeline`) and the helpers (`/etl-design-status`,
  `/finalize-requirements`, `/validate-config`, `/etl-design-help`).
- That Phases 3-5 scaffold skeletons and write plans - they never execute
  anything (no `terraform apply`, no deploy, no `git push`, no test runs);
  those are human steps.
- The difference between a skill, a subagent, a slash command and the
  SessionStart hook in this harness, and when each runs.
- The exact next command for my current state (check `state/active-workspace`
  then `<workspace>/progress.json`).

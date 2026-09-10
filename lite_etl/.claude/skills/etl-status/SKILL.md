---
name: etl-status
description: Show the active project, its phase, and the next command.
---

# etl-status

Read `state/active`, then `projects/<active>/progress.json`. Print one block:

    project: <name>   engine: <engine>   phase: <spec|design|build>
    next: <one command>

`next` map: no active project → `/etl-spec <name>` · phase spec → `/etl-design` ·
phase design → `/etl-build` · phase build → `cd projects/<name>/repo && make demo`.

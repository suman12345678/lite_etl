---
name: etl-design
description: Phase 2. Turn spec.md into design.md + diagram.md.
---

# etl-design

1. Read `projects/<active>/spec.md` (path in `state/active`). Missing → tell the user to run `/etl-spec`, stop.
2. Write `design.md` from `templates/design.md`: approach, component table (one row per real component,
   each naming its spec ref), decisions (`<choice> because <spec item>`), and the "Maps to spec" line.
3. Write `diagram.md` — one ```mermaid flowchart: sources → raw → staging → marts → rules gate → publish,
   with the orchestrator and the rule checkpoints shown.
4. Check every Sources / Target / Transforms / Rules item appears in `design.md`. List gaps; don't hide them.
5. `progress.json` → `"phase": "design"`. Say `/etl-build` is next.

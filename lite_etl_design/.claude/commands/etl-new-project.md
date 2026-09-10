---
description: Create (or switch to) a project workspace where this harness will write its deliverables
argument-hint: <name | relative/path | C:\absolute\path>
---

Set up the **project workspace** for a new ETL data-harness design, or switch the
active workspace to an existing one. Target: `$ARGUMENTS`

## Resolve the target directory

1. If `$ARGUMENTS` is empty, ask me for a project name or path and stop.
2. Normalise:
   - no path separator (e.g. `sales-dwh`) -> `./projects/sales-dwh/` (a subfolder
     of the harness)
   - a relative path with a separator (e.g. `../work/sales-dwh`) -> resolve
     relative to the harness root
   - an absolute path (e.g. `C:\work\sales-dwh-design`) -> use as-is
   The workspace can live anywhere - a subfolder or a completely separate folder.

## If the target already contains `project.json`

Do **not** overwrite anything. Just write that path into
`state/active-workspace` and tell me the project is now active, plus its phase
status from `<target>/progress.json`.

## Otherwise, scaffold it

Create:

- `<target>/intake/`            (I drop existing source docs here)
- `<target>/requirements/`      (Phase 1 deliverables land here)
- `<target>/design/`            (Phase 2 deliverables land here)
- `<target>/notes/`             (optional interview transcripts / scratch)

(Phases 3-5 create their own folders when run: `build/` incl. `build/repo/`,
`pipeline/`, `hardening/`.)
- `<target>/project.json`:
  ```json
  {
    "name": "<project name>",
    "created": "<today's date>",
    "harness_path": "<absolute path of this harness>",
    "harness_version": "0.1"
  }
  ```
- `<target>/progress.json` - copy `state/progress.template.json`, then set
  `project_name`, `workspace_path` (the resolved path), and `created` = today.
- `<target>/README.md` - a short note: what this folder is, that templates and
  commands come from the harness at `<harness_path>`, and the command sequence
  (`/gather-requirements` -> `/design-architecture`).

Then write the resolved absolute path into `state/active-workspace` (one line,
no trailing content).

## Report

Tell me: the workspace path, that it is now the active project, and that the next
step is `/gather-requirements` (then `/design-architecture` -> `/build-components`
-> `/assemble-pipeline` -> `/harden-pipeline`). Point me at `MAP.md` for the full
picture.

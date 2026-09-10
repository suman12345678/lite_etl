# Component buildsheet: `<component name>`

> Phase 3 deliverable. One per component in the build plan. The concrete spec a
> developer (or Claude) follows to implement and test this component.

- **Design refs:** `design/component-design.md#<component>`, plus
  `requirements/<nn>.md` items it satisfies
- **Language / framework:** (from `10-platform-and-deployment.md` / design)
- **Repo path:** `build/repo/<path>/`

## Files to create

| Path | Purpose |
|------|---------|
| `build/repo/<path>/<file>` | |
| `build/repo/tests/unit/<test file>` | |
| `build/repo/<path>/config.example.<ext>` | sample config, no secrets |

## Public interface

- **Entry point:** function / CLI / class - signature
- **Inputs:** parameters, config keys (name, type, default, required?), state read
- **Outputs:** datasets/paths written, markers, metrics emitted, lineage events,
  state written, return value / exit code
- **Config keys:**

  | Key | Type | Default | Required | Notes |
  |-----|------|---------|----------|-------|
  | | | | | |

## Key logic (steps to implement)

1.
2.
3.

## Unit tests to write

| Test | Fixture | Asserts |
|------|---------|---------|
| happy path | `fixtures/<source>/sample.*` | rows/shape/markers as expected |
| idempotent re-run | same input twice | second run = no new side effects |
| failure: `<mode 1>` | `fixtures/<source>/<edge>.*` | detected + handled per design |
| failure: `<mode 2>` | | |
| edge: late data | | |
| edge: duplicates | | |
| edge: schema drift | | halts / warns per policy |
| edge: nulls / encoding | | |

## Fixtures needed

_List each fixture file this component's tests require; add to
`fixtures-catalog.md` if new._

## Done checklist

- [ ] files created  - [ ] interface matches  - [ ] all tests above pass
- [ ] runs locally (no cloud)  - [ ] metrics + lineage emitted
- [ ] config-driven  - [ ] wired into the test runner + CI job

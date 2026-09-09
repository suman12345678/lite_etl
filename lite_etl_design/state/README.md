# state/ - harness-local pointers

The harness itself is stateless about *your* project. It only remembers **which
project is active**.

| File | Purpose | Tracked in git? |
|------|---------|-----------------|
| `active-workspace` | one line: the path of the current project workspace. Written by `/etl-new-project`, read by every other command and by the session hook. | no (machine-local) |
| `progress.template.json` | the starting `progress.json` copied into each new workspace. | yes |

Per-project progress lives in `<workspace>/progress.json`, not here. Switching
projects = pointing `active-workspace` at a different folder (run
`/etl-new-project` with an existing path).

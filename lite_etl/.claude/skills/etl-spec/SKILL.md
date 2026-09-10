---
name: etl-spec
description: Phase 1. Interview the user, write projects/<name>/spec.md from templates/spec.md.
---

# etl-spec

1. Project name from args, else ask. `mkdir -p projects/<name>`; write that path to `state/active`.
   If `spec.md` already exists, load it and revise instead of starting over.
2. Ask only what `templates/spec.md` needs, one topic at a time:
   engine → sources → target model → transforms → rules → schedule → non-functional → pii.
   Move on when a field has an answer or an explicit "n/a".
3. Write `projects/<name>/spec.md`. Anything undecided goes under `## Open questions` — never guessed.
4. Write `progress.json`: `{ "phase": "spec", "engine": "<engine>", "updated": "<date>" }`.
   Say `/etl-design` is next.

Rules: no invented hostnames, credentials, or volumes. Stay inside the template's fields.

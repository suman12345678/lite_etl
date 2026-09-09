---
description: Phase 1 wrap-up - synthesize interview notes and intake docs into the requirement files
argument-hint: [none]
---

Finalize **Phase 1 - Requirements** without re-running the whole interview.

Use this when the interview already happened (in this conversation or captured in
the active workspace's `intake/`) and you just need the deliverables written and
checked.

1. Resolve the active workspace `<WS>` from `state/active-workspace` (stop and
   tell me to run `/etl-new-project` if there is none).
2. Invoke the `gather-etl-requirements` skill, Step 2 onward.
3. Optionally run the `requirements-synthesizer` subagent (pass it `<WS>`) to
   draft `<WS>/requirements/*.md` from the notes, then review every file.
4. Make sure `<WS>/requirements/99-open-questions.md` lists every gap and assumption.
5. Update `<WS>/progress.json` (phase 1 status, deliverables, open-question count).
6. Show me the final file list and the open questions.

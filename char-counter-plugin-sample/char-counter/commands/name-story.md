---
description: Write a 5-sentence story about a name
argument-hint: <name>
---

The user wants a short story about the name: `$ARGUMENTS`

If `$ARGUMENTS` is empty, ask the user for the name first and stop.

Otherwise, launch the `name-storyteller` subagent (use the Agent tool with
`subagent_type: "name-storyteller"`) and give it the name. When it returns,
relay its 5-sentence story to the user verbatim.

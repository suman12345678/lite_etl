---
description: Count how many characters are in a name using a Python script
argument-hint: <name>
---

The user wants to know how many characters are in a name.

The name they provided is: `$ARGUMENTS`

If `$ARGUMENTS` is empty, ask the user for the name first.

Otherwise, run the plugin's Python script with the name as an argument:

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/count_chars.py" "$ARGUMENTS"
```

(If `python` is not found, try `python3`.)

Then display the script's output to the user in a clear, friendly summary.

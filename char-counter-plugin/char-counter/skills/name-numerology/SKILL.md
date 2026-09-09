---
name: name-numerology
description: Compute playful "name numerology" and letter stats for a name — vowel/consonant split, initials, reversed spelling, Pythagorean numerology sum and destiny number. Use when someone wants fun facts, a numerology reading, or a letter breakdown of a name.
---

# Name numerology

This is for fun, not a real reading. Keep the tone light.

## Steps

1. Run the helper script (use `python3` if `python` is not found):

   ```
   python "${CLAUDE_PLUGIN_ROOT}/scripts/name_facts.py" "<name>"
   ```

2. Present the script output as a short bulleted list.

3. Add one friendly sentence interpreting the destiny number, clearly framed as
   entertainment.

If no name is given, ask for one first.

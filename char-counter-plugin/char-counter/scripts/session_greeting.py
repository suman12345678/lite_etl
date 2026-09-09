#!/usr/bin/env python3
"""SessionStart hook for the char-counter plugin.

Whatever this prints on stdout is added to the session as context, so Claude
knows the plugin is loaded and what it offers.
"""

print(
    "[char-counter plugin loaded] "
    "Commands: /count-chars <name>, /name-story <name>. "
    "Skills: name-numerology, name-acrostic. "
    "MCP tool: search_name (live web search for a name)."
)

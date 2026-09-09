# char-counter plugin

A small Claude Code plugin built as a **tour of every part a plugin can have**.
The original job — "give it a name, it counts the characters" — is still here,
plus one example of each other component type.

## What's inside

| Part | File(s) | What it does |
|------|---------|--------------|
| **Command** | `commands/count-chars.md` | `/count-chars <name>` — runs a Python script and reports character counts |
| **Command** | `commands/name-story.md` | `/name-story <name>` — hands the name to the storyteller agent |
| **Agent** | `agents/name-storyteller.md` | Writes an exactly-5-sentence story about the name |
| **Skill** | `skills/name-numerology/SKILL.md` | Playful numerology + letter stats (script-backed) |
| **Skill** | `skills/name-acrostic/SKILL.md` | Writes an acrostic poem from the name (pure instructions, no script) |
| **Hook** | `hooks/hooks.json` | `SessionStart` hook that announces the plugin and its commands |
| **MCP server** | `.mcp.json` + `scripts/search_name.py` | Tool `search_name` — live web search for a name (pure-stdlib stdio MCP server) |
| **Scripts** | `scripts/*.py` | The Python behind the command, the skill, the hook, and the MCP server |

## Structure

```
char-counter-plugin/
├── .claude-plugin/
│   └── marketplace.json          # local marketplace so the plugin is installable
└── char-counter/                 # the plugin itself
    ├── .claude-plugin/
    │   └── plugin.json           # plugin manifest
    ├── .mcp.json                 # registers the name-web-search MCP server
    ├── commands/
    │   ├── count-chars.md        # /count-chars
    │   └── name-story.md         # /name-story
    ├── agents/
    │   └── name-storyteller.md   # 5-sentence story agent
    ├── skills/
    │   ├── name-numerology/
    │   │   └── SKILL.md
    │   └── name-acrostic/
    │       └── SKILL.md
    ├── hooks/
    │   └── hooks.json            # SessionStart greeting
    └── scripts/
        ├── count_chars.py        # counting
        ├── name_facts.py         # numerology skill
        ├── session_greeting.py   # hook
        └── search_name.py        # MCP server (stdio, no dependencies)
```

## Install (local)

In Claude Code:

```
/plugin marketplace add C:\Users\sahaa\suman_on_computer\claude\char-counter-plugin
/plugin install char-counter@char-counter-marketplace
```

Restart Claude Code if prompted. On start you'll see the hook's greeting line.

## Use

```
/count-chars Ada Lovelace          # character counts
/name-story Ada Lovelace           # 5-sentence story via the agent
```

Ask naturally to trigger the skills or the MCP tool:

- "give me the name numerology for Ada Lovelace"  → `name-numerology` skill
- "write an acrostic for Ada Lovelace"            → `name-acrostic` skill
- "web-search the name Ada Lovelace"              → MCP tool `search_name`

## Run the pieces directly (no plugin)

```
python char-counter/scripts/count_chars.py "Ada Lovelace"
python char-counter/scripts/name_facts.py  "Ada Lovelace"

# MCP server: talks JSON-RPC on stdin/stdout
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"search_name","arguments":{"name":"Ada Lovelace"}}}' \
  | python char-counter/scripts/search_name.py
```

The MCP server uses only the Python standard library. It does a live DuckDuckGo
search and, if the network is unavailable, falls back to returning ready-made
search-engine links.

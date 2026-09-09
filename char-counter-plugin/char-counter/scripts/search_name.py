#!/usr/bin/env python3
"""A tiny stdio MCP server that runs a web search for a name.

Pure standard library, no dependencies. Speaks the JSON-RPC 2.0 / MCP
"stdio" transport: one JSON message per line on stdin, one per line on stdout.

Exposes a single tool:
    search_name(name: str) -> top web results (titles + URLs)

It tries a live DuckDuckGo HTML search; if the network is unavailable it
falls back to returning ready-made search-engine links for the name.
"""

import html
import json
import re
import sys
import urllib.parse
import urllib.request

SERVER_NAME = "name-web-search"
SERVER_VERSION = "1.0.0"
PROTOCOL_VERSION = "2024-11-05"

TOOLS = [
    {
        "name": "search_name",
        "description": (
            "Run a web search for a given name (or phrase) and return the top "
            "result titles and URLs."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The name or phrase to search the web for.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max number of results (default 5).",
                },
            },
            "required": ["name"],
        },
    }
]


def _unwrap(href):
    """DuckDuckGo wraps outbound links as //duckduckgo.com/l/?uddg=<encoded>."""
    href = html.unescape(href)
    parsed = urllib.parse.urlparse(href if "//" in href else "https:" + href)
    params = urllib.parse.parse_qs(parsed.query)
    if "uddg" in params:
        return params["uddg"][0]
    return href


def ddg_search(query, limit=5):
    url = "https://lite.duckduckgo.com/lite/?q=" + urllib.parse.quote(query)
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (name-web-search MCP server)"}
    )
    with urllib.request.urlopen(req, timeout=12) as resp:
        body = resp.read().decode("utf-8", "replace")

    results = []
    seen = set()
    for match in re.finditer(r"<a\b([^>]*)>(.*?)</a>", body, re.S):
        attrs, inner = match.group(1), match.group(2)
        if "result-link" not in attrs:
            continue
        href_match = re.search(r'href="([^"]+)"', attrs)
        if not href_match:
            continue
        href = _unwrap(href_match.group(1))
        title = html.unescape(re.sub(r"<[^>]+>", "", inner)).strip()
        if not title or href in seen:
            continue
        seen.add(href)
        results.append({"title": title, "url": href})
        if len(results) >= limit:
            break
    return results


def fallback_links(query):
    q = urllib.parse.quote(query)
    return [
        {"title": "DuckDuckGo", "url": f"https://duckduckgo.com/?q={q}"},
        {"title": "Google", "url": f"https://www.google.com/search?q={q}"},
        {"title": "Bing", "url": f"https://www.bing.com/search?q={q}"},
        {"title": "Wikipedia", "url": f"https://en.wikipedia.org/w/index.php?search={q}"},
    ]


def do_search(name, limit=5):
    name = (name or "").strip()
    if not name:
        return "No name provided."
    try:
        limit = max(1, min(int(limit), 10))
    except (TypeError, ValueError):
        limit = 5

    lines = [f'Web search for: "{name}"', ""]
    try:
        results = ddg_search(name, limit)
        if not results:
            raise RuntimeError("no results parsed from response")
        lines.append("Top results:")
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. {r['title']}")
            lines.append(f"   {r['url']}")
    except Exception as exc:  # noqa: BLE001 - degrade gracefully offline
        lines.append(f"(Live search unavailable: {exc}. Use these links instead.)")
        for r in fallback_links(name):
            lines.append(f"- {r['title']}: {r['url']}")
    return "\n".join(lines)


def handle(msg):
    method = msg.get("method")
    mid = msg.get("id")

    if method == "initialize":
        return _ok(mid, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        })

    if method == "tools/list":
        return _ok(mid, {"tools": TOOLS})

    if method == "tools/call":
        params = msg.get("params") or {}
        args = params.get("arguments") or {}
        if params.get("name") == "search_name":
            text = do_search(args.get("name"), args.get("limit", 5))
            return _ok(mid, {"content": [{"type": "text", "text": text}]})
        return _err(mid, -32602, f"Unknown tool: {params.get('name')}")

    if method == "ping":
        return _ok(mid, {})

    if mid is None:
        return None  # a notification (e.g. notifications/initialized) - no reply

    return _err(mid, -32601, f"Method not found: {method}")


def _ok(mid, result):
    return {"jsonrpc": "2.0", "id": mid, "result": result}


def _err(mid, code, message):
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": message}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle(msg)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()

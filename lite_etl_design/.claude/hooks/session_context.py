#!/usr/bin/env python3
"""SessionStart hook for the lite-etl-design harness.

Prints a one-line orientation: which project workspace is active, which design
phase it is in, what has been delivered, and whether anything is waiting in the
workspace's intake/ folder.

Pure standard library. Never raises - a hook that crashes blocks the session.
"""
from __future__ import annotations

import json
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[2]
POINTER = HARNESS / "state" / "active-workspace"


def _count(folder: Path) -> int:
    if not folder.exists():
        return 0
    return len([p for p in folder.glob("*") if p.is_file() and p.name != ".gitkeep"])


def _resolve_workspace() -> Path | None:
    try:
        raw = POINTER.read_text(encoding="utf-8").strip()
    except Exception:
        return None
    if not raw:
        return None
    ws = Path(raw)
    if not ws.is_absolute():
        ws = (HARNESS / ws).resolve()
    return ws if (ws / "project.json").exists() else None


def _phase_line(progress: dict) -> str:
    phases = progress.get("phases", {})
    parts = []
    for key, val in phases.items():
        status = val.get("status", "?") if isinstance(val, dict) else str(val)
        parts.append(f"{key}={status}")
    return " | ".join(parts) or "no phases recorded"


def main() -> None:
    print(
        "[lite-etl-design] Step-by-step ETL data-harness design. "
        "Commands: /etl-new-project /gather-requirements /finalize-requirements "
        "/design-architecture /build-components /assemble-pipeline "
        "/validate-config /harden-pipeline /etl-design-status /etl-design-help  |  see MAP.md"
    )

    ws = _resolve_workspace()
    if ws is None:
        print(
            "[lite-etl-design] no active project. Start one with "
            "/etl-new-project <name>  (creates ./projects/<name>/ or use a full path)."
        )
        return

    try:
        proj = json.loads((ws / "project.json").read_text(encoding="utf-8"))
        name = proj.get("name", ws.name)
    except Exception:
        name = ws.name

    print(f"[lite-etl-design] active project: {name}  ({ws})")

    try:
        progress = json.loads((ws / "progress.json").read_text(encoding="utf-8"))
        print(f"[lite-etl-design] phases: {_phase_line(progress)}")
    except Exception:
        print("[lite-etl-design] progress.json not readable yet")

    pending = _count(ws / "intake")
    if pending:
        names = ", ".join(
            p.name for p in (ws / "intake").glob("*")
            if p.is_file() and p.name != ".gitkeep"
        )
        print(f"[lite-etl-design] {ws.name}/intake has {pending} file(s) to read: {names}")

    req_n, des_n = _count(ws / "requirements"), _count(ws / "design")
    print(
        f"[lite-etl-design] delivered: {req_n} requirement file(s), {des_n} design "
        "file(s). Next: run /etl-design-status."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # pragma: no cover - defensive
        print(f"[lite-etl-design] session hook skipped: {exc}")

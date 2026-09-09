"""Landing-zone writer.

Folder-based for now:  landing/<source>/<run_date>/<run_id>/{data.csv, rejects.csv,
_manifest.json, _reconciliation.json}  plus an append-only landing/_runs.jsonl log.

To land in cloud object storage later (S3 / GCS / Azure Blob), replace the body
of write_dataset() / write_json() with an upload - the rest of the pipeline does
not care where the bytes go.
"""
from __future__ import annotations

import csv
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def new_run_id(now: datetime | None = None) -> str:
    now = now or utcnow()
    return "run_" + now.strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:6]


def run_dir(landing_zone: Path, source_name: str, run_id: str,
            now: datetime | None = None) -> Path:
    now = now or utcnow()
    return Path(landing_zone) / source_name / now.strftime("%Y-%m-%d") / run_id


def _fieldnames(rows: list[dict], include_private: bool = False) -> list[str]:
    names: list[str] = []
    for r in rows:
        for k in r:
            if k in names:
                continue
            if not include_private and k.startswith("_"):
                continue
            names.append(k)
    return names


def write_dataset(target_dir: Path, rows: list[dict], filename: str = "data.csv",
                  include_private: bool = False) -> Path:
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / filename
    fieldnames = _fieldnames(rows, include_private=include_private)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_json(target_dir: Path, name: str, payload: dict) -> Path:
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / name
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def append_run_log(landing_zone: Path, record: dict) -> None:
    lz = Path(landing_zone)
    lz.mkdir(parents=True, exist_ok=True)
    with (lz / "_runs.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, default=str) + "\n")

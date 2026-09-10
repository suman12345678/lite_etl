"""Per-run manifest.json. Buildsheet: component-buildsheet-landing.md

Stub - Phase 3 scaffold. Implement against the matching buildsheet.
"""

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Manifest:
    source: str
    object: str
    run_id: str
    business_date: str
    window: dict = field(default_factory=dict)
    row_count: int = 0
    checksums: dict = field(default_factory=dict)
    source_files: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        raise NotImplementedError  # TODO


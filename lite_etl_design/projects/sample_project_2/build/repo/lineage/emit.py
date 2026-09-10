"""Assemble + send OpenLineage events for a run. Buildsheet: component-buildsheet-lineage.md

Stub - Phase 3 scaffold. Implement against the matching buildsheet.
"""

from __future__ import annotations
from pathlib import Path
from datetime import date


def emit(run_id: str, business_date: date, manifests: list[Path],
         dbt_manifest: Path, settings) -> None:
    # TODO parse manifests + dbt manifest -> RunEvents (column-lineage facet); best-effort POST
    raise NotImplementedError


def trace(gold_table: str, key: str):
    raise NotImplementedError  # TODO dev helper: source run_id(s), files, model SHA, recon uri


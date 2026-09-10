"""Commit the reconciled business date; advance watermark last. Buildsheet: component-buildsheet-publisher.md

Stub - Phase 3 scaffold. Implement against the matching buildsheet.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date


class ReconciliationNotPassed(Exception):
    ...


@dataclass
class PublishResult:
    groups_committed: list[str] = field(default_factory=list)
    delta_versions: dict = field(default_factory=dict)
    success_marker_uri: str | None = None


def publish(business_date: date, run_id: str, target: str, recon, settings) -> PublishResult:
    if getattr(recon, "verdict", None) != "PASS":
        raise ReconciliationNotPassed(business_date)
    # TODO per-group transaction -> _SUCCESS -> lineage.emit -> StateStore.commit_watermark(run_id)
    raise NotImplementedError


def rollback(business_date: date, target: str, to_version: dict, settings) -> None:
    raise NotImplementedError  # TODO Delta RESTORE ... TO VERSION AS OF per table


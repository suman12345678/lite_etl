"""Watermark + run registry (_state.watermarks Delta; local = parquet dir). Buildsheet: component-buildsheet-config.md

Stub - Phase 3 scaffold. Implement against the matching buildsheet.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import date


@dataclass
class Watermark:
    source: str
    object: str
    value: str
    type: str


class StateStore:
    def __init__(self, settings) -> None:
        self.settings = settings

    def get_watermark(self, source: str, object: str) -> Watermark | None:
        raise NotImplementedError  # TODO latest COMMITTED row

    def stage_watermark(self, source: str, object: str, value: str, run_id: str) -> None:
        raise NotImplementedError  # TODO upsert with committed_at = NULL

    def commit_watermark(self, run_id: str) -> None:
        raise NotImplementedError  # TODO called by publisher after reconcile PASS

    def register_run(self, run_id: str, source: str, business_date: date, status: str) -> None:
        raise NotImplementedError  # TODO


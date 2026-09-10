"""Extractor ABC + shared retry/paging/manifest helpers. Buildsheet: component-buildsheet-extractor.md

Stub - Phase 3 scaffold. Implement against the matching buildsheet.
"""

from __future__ import annotations
import abc
from dataclasses import dataclass, field
from datetime import date


@dataclass
class ExtractPlan:
    source: str
    business_date: date
    run_id: str
    params: dict = field(default_factory=dict)


@dataclass
class ExtractResult:
    rows: int
    files: list[str]
    checksums: dict
    new_watermark: str | None
    warnings: list[str] = field(default_factory=list)


class ExtractFailed(Exception):
    ...


class Extractor(abc.ABC):
    source: str

    def __init__(self, settings, state, secrets) -> None:
        self.settings, self.state, self.secrets = settings, state, secrets

    @abc.abstractmethod
    def plan(self, business_date: date, run_id: str) -> ExtractPlan: ...

    @abc.abstractmethod
    def run(self, plan: ExtractPlan) -> ExtractResult: ...


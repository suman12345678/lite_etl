"""Run tag:recon tests + compare -> PASS/FAIL; exit non-zero on FAIL. Buildsheet: component-buildsheet-reconciliation.md

Stub - Phase 3 scaffold. Implement against the matching buildsheet.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date


@dataclass
class CheckResult:
    name: str
    applies_to: str
    expected: float
    actual: float
    delta: float
    tolerance: float
    verdict: str
    detail: str = ""


@dataclass
class ReconResult:
    verdict: str  # "PASS" | "FAIL"
    checks: list[CheckResult] = field(default_factory=list)
    report_uri: str | None = None


def run_gate(business_date: date, run_id: str, target: str, settings) -> ReconResult:
    # TODO 1) dbt test tag:recon  2) compare.row_count_identity  3) report.build  4) verdict
    raise NotImplementedError


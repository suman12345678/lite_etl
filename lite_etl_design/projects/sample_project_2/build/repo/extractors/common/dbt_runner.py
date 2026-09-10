"""Thin dbt build/test wrapper. Buildsheet: component-buildsheet-dbt-runner.md

Stub - Phase 3 scaffold. Implement against the matching buildsheet.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date


class FullRefreshNotAllowed(Exception):
    ...


@dataclass
class DbtResult:
    ok: bool
    models_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    failed_nodes: list[str] = field(default_factory=list)
    manifest_path: str | None = None


def run_build(select: str, target: str, business_date: date, run_id: str, *,
              defer_state: str | None = None, full_refresh: bool = False) -> DbtResult:
    """Assemble & run `dbt build --select ... --target ... --vars {...}`; parse run_results.json."""
    raise NotImplementedError  # TODO


def run_tests(select: str, target: str) -> DbtResult:
    raise NotImplementedError  # TODO `dbt test --select <select>` (used by recon for tag:recon)


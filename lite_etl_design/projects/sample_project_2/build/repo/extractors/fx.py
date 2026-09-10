"""fx extractor - shape D. open.er-api.com single GET; carry-forward on gap. Buildsheet: component-buildsheet-extractor.md

Stub - Phase 3 scaffold. Implement against the matching buildsheet.
"""

from __future__ import annotations
from datetime import date

from extractors.common.base import Extractor, ExtractPlan, ExtractResult


class FxExtractor(Extractor):
    source = "fx"

    def plan(self, business_date: date, run_id: str) -> ExtractPlan:
        # TODO resolve watermark / file list / API params (open.er-api.com single GET; carry-forward on gap)
        raise NotImplementedError

    def run(self, plan: ExtractPlan) -> ExtractResult:
        # TODO fetch -> Parquet -> row counts + checksums + new high-watermark (staged, not committed)
        raise NotImplementedError


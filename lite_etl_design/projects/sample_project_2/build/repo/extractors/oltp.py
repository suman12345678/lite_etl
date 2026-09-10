"""oltp extractor - shape A. Postgres incremental (updated_at, 60-min lookback): customers, products, orders, order_lines. Buildsheet: component-buildsheet-extractor.md

Stub - Phase 3 scaffold. Implement against the matching buildsheet.
"""

from __future__ import annotations
from datetime import date

from extractors.common.base import Extractor, ExtractPlan, ExtractResult


class OltpExtractor(Extractor):
    source = "oltp"

    def plan(self, business_date: date, run_id: str) -> ExtractPlan:
        # TODO resolve watermark / file list / API params (Postgres incremental (updated_at, 60-min lookback): customers, products, orders, order_lines)
        raise NotImplementedError

    def run(self, plan: ExtractPlan) -> ExtractResult:
        # TODO fetch -> Parquet -> row counts + checksums + new high-watermark (staged, not committed)
        raise NotImplementedError


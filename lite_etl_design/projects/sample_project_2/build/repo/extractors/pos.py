"""pos extractor - shape B. S3 CSV.gz per store; gunzip+parse (cents/100, tz->UTC); _file_etag for supersede. Buildsheet: component-buildsheet-extractor.md

Stub - Phase 3 scaffold. Implement against the matching buildsheet.
"""

from __future__ import annotations
from datetime import date

from extractors.common.base import Extractor, ExtractPlan, ExtractResult


class PosExtractor(Extractor):
    source = "pos"

    def plan(self, business_date: date, run_id: str) -> ExtractPlan:
        # TODO resolve watermark / file list / API params (S3 CSV.gz per store; gunzip+parse (cents/100, tz->UTC); _file_etag for supersede)
        raise NotImplementedError

    def run(self, plan: ExtractPlan) -> ExtractResult:
        # TODO fetch -> Parquet -> row counts + checksums + new high-watermark (staged, not committed)
        raise NotImplementedError


"""salesforce extractor - shape A. Bulk API 2.0: Account/Contact/Opportunity(+lines); SystemModstamp; queryAll for deletes. Buildsheet: component-buildsheet-extractor.md

Stub - Phase 3 scaffold. Implement against the matching buildsheet.
"""

from __future__ import annotations
from datetime import date

from extractors.common.base import Extractor, ExtractPlan, ExtractResult


class SalesforceExtractor(Extractor):
    source = "salesforce"

    def plan(self, business_date: date, run_id: str) -> ExtractPlan:
        # TODO resolve watermark / file list / API params (Bulk API 2.0: Account/Contact/Opportunity(+lines); SystemModstamp; queryAll for deletes)
        raise NotImplementedError

    def run(self, plan: ExtractPlan) -> ExtractResult:
        # TODO fetch -> Parquet -> row counts + checksums + new high-watermark (staged, not committed)
        raise NotImplementedError


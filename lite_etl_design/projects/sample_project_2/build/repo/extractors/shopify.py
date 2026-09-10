"""shopify extractor - shape A. Shopify Admin REST: orders/refunds/fulfillments; cursor pagination; drop test=true. Buildsheet: component-buildsheet-extractor.md

Stub - Phase 3 scaffold. Implement against the matching buildsheet.
"""

from __future__ import annotations
from datetime import date

from extractors.common.base import Extractor, ExtractPlan, ExtractResult


class ShopifyExtractor(Extractor):
    source = "shopify"

    def plan(self, business_date: date, run_id: str) -> ExtractPlan:
        # TODO resolve watermark / file list / API params (Shopify Admin REST: orders/refunds/fulfillments; cursor pagination; drop test=true)
        raise NotImplementedError

    def run(self, plan: ExtractPlan) -> ExtractResult:
        # TODO fetch -> Parquet -> row counts + checksums + new high-watermark (staged, not committed)
        raise NotImplementedError


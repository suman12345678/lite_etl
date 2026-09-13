"""Unit tests for extract/billing.py against recorded fixtures. No network, no creds --
`_get` (the only function that would hit the real API) is patched out."""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

FIXTURES = Path(__file__).resolve().parents[1] / "extract" / "fixtures"

os.environ.setdefault("BILLING_API_BASE_URL", "https://billing.example.test")
os.environ.setdefault("BILLING_API_TOKEN", "test-token-not-real")

from extract import billing  # noqa: E402


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


class FakeSink:
    def __init__(self):
        self.appended: list[tuple] = []

    def append_rows(self, table, columns, rows):
        self.appended.append((table, columns, list(rows)))
        return len(list(rows))

    def close(self):
        pass


class TestPagination(unittest.TestCase):
    def test_paginate_walks_every_page(self):
        pages = [_load("billing_invoices_page1.json"), _load("billing_invoices_page2.json")]
        with patch.object(billing, "_get", side_effect=pages):
            rows = list(billing._paginate(session=object(), path="/v1/invoices", since=None))
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0]["id"], "INV00101")
        self.assertEqual(rows[-1]["id"], "INV00103")

    def test_paginate_stops_when_has_more_false(self):
        page = _load("billing_subscriptions_page1.json")
        with patch.object(billing, "_get", side_effect=[page]):
            rows = list(billing._paginate(session=object(), path="/v1/subscriptions", since=None))
        self.assertEqual(len(rows), 2)


class TestRowParsing(unittest.TestCase):
    def test_invoice_row_shape_and_types(self):
        raw = _load("billing_invoices_page1.json")["data"][0]
        row = billing._invoice_row(raw)
        self.assertEqual(len(row), len(billing.INVOICE_COLUMNS))
        self.assertEqual(row[0], "INV00101")
        self.assertEqual(row[4], "USD")  # currency uppercased
        self.assertIsInstance(row[5], float)  # amount_local cast to float

    def test_subscription_row_handles_null_end_date(self):
        raw = _load("billing_subscriptions_page1.json")["data"][0]
        row = billing._subscription_row(raw)
        self.assertEqual(row[0], "S002")
        self.assertIsNone(row[4])  # end_date null for an open subscription


class TestLandInvoices(unittest.TestCase):
    def test_land_invoices_appends_rows_and_advances_watermark(self):
        pages = [_load("billing_invoices_page1.json"), _load("billing_invoices_page2.json")]
        fake_sink = FakeSink()
        watermarks: dict[str, str] = {}

        def fake_get_watermark(sink, source):
            return watermarks.get(source)

        def fake_set_watermark(sink, source, value):
            watermarks[source] = value

        with patch.object(billing, "_get", side_effect=pages), \
             patch.object(billing, "get_watermark", side_effect=fake_get_watermark), \
             patch.object(billing, "set_watermark", side_effect=fake_set_watermark):
            n = billing.land_invoices(fake_sink, session=object())

        self.assertEqual(n, 3)
        self.assertEqual(len(fake_sink.appended), 1)
        table, columns, rows = fake_sink.appended[0]
        self.assertEqual(table, "billing_invoices")
        self.assertEqual(columns, billing.INVOICE_COLUMNS)
        self.assertEqual(len(rows), 3)
        # webhook-retry-style late update should have advanced the watermark
        self.assertEqual(watermarks["billing.invoices"], "2026-07-18T22:00:00Z")


if __name__ == "__main__":
    unittest.main()

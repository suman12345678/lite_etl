"""Unit tests for extract/ref.py against recorded CSV fixtures. No real S3 --
extract.ref._s3() is patched with a fake client that serves the fixture bytes."""

from __future__ import annotations

import io
import os
import unittest
from pathlib import Path
from unittest.mock import patch

FIXTURES = Path(__file__).resolve().parents[1] / "extract" / "fixtures"

os.environ.setdefault("REF_S3_BUCKET", "example-ref-bucket-test")

from extract import ref  # noqa: E402


class FakeS3Client:
    def __init__(self, files: dict[str, bytes]):
        self.files = files

    def get_object(self, Bucket, Key):  # noqa: N803 - mirrors boto3's signature
        return {"Body": io.BytesIO(self.files[Key])}


class TestFetchPlans(unittest.TestCase):
    def test_fetch_plans_parses_every_row(self):
        content = (FIXTURES / "ref_plans.csv").read_bytes()
        fake = FakeS3Client({"ref/plans.csv": content})
        with patch.object(ref, "_s3", return_value=fake):
            rows = list(ref.fetch_plans())
        self.assertEqual(len(rows), 4)
        basic = next(r for r in rows if r[0] == "BASIC")
        self.assertEqual(basic, ("BASIC", 50.0, "starter", 0))
        retired = next(r for r in rows if r[0] == "PROMO_2024")
        self.assertEqual(retired[3], 1)  # is_retired cast to int


class TestFetchFxRates(unittest.TestCase):
    def test_fetch_fx_rates_uppercases_currency_and_casts_rate(self):
        content = (FIXTURES / "ref_fx_rates.csv").read_bytes()
        fake = FakeS3Client({"ref/fx_rates.csv": content})
        with patch.object(ref, "_s3", return_value=fake):
            rows = list(ref.fetch_fx_rates())
        self.assertEqual(len(rows), 5)
        self.assertIn(("2026-06-01", "GBP", 1.27), rows)
        # the July gap noted in Sources -> no GBP row for 2026-07 in this fixture
        july_gbp = [r for r in rows if r[0].startswith("2026-07") and r[1] == "GBP"]
        self.assertEqual(july_gbp, [])


if __name__ == "__main__":
    unittest.main()

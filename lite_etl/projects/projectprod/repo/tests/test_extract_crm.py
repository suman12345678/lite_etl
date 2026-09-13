"""Unit tests for extract/crm.py against recorded fixtures. No real Postgres --
the connection object is a fake; only fetch_accounts/land_accounts are exercised."""

from __future__ import annotations

import json
import os
import unittest
from pathlib import Path

FIXTURES = Path(__file__).resolve().parents[1] / "extract" / "fixtures"

os.environ.setdefault("CRM_DB_HOST", "crm-db.example.test")
os.environ.setdefault("CRM_DB_PORT", "5432")
os.environ.setdefault("CRM_DB_NAME", "crm")
os.environ.setdefault("CRM_DB_USER", "test-user")
os.environ.setdefault("CRM_DB_PASSWORD", "test-password-not-real")

from extract import crm  # noqa: E402
from extract.common import ConfigError  # noqa: E402


class FakeCursor:
    def __init__(self, rows):
        self._rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, query):
        self.query = query

    def __iter__(self):
        return iter(self._rows)


class FakeConn:
    def __init__(self, rows):
        self._rows = rows

    def cursor(self):
        return FakeCursor(self._rows)


class FakeSink:
    def __init__(self):
        self.replaced = []

    def replace_rows(self, table, columns, rows):
        rows = list(rows)
        self.replaced.append((table, columns, rows))
        return len(rows)


class TestFetchAccounts(unittest.TestCase):
    def setUp(self):
        self.rows = json.loads((FIXTURES / "crm_accounts.json").read_text())
        self.rows = [tuple(r) for r in self.rows]

    def test_fetch_accounts_yields_every_row(self):
        conn = FakeConn(self.rows)
        out = list(crm.fetch_accounts(conn))
        self.assertEqual(out, self.rows)

    def test_land_accounts_stamps_loaded_at_and_full_replaces(self):
        conn = FakeConn(self.rows)
        sink = FakeSink()
        n = crm.land_accounts(sink, conn)
        self.assertEqual(n, len(self.rows))
        table, columns, landed_rows = sink.replaced[0]
        self.assertEqual(table, "crm_accounts")
        self.assertEqual(columns, crm.ACCOUNT_COLUMNS)
        for row in landed_rows:
            self.assertEqual(len(row), len(crm.ACCOUNT_COLUMNS))
            self.assertTrue(row[-1])  # loaded_at stamped, non-empty

        # the merged row (A013 -> A007) must survive extraction unresolved --
        # resolving merges is a staging-boundary concern (stg_crm__accounts), not extract's.
        merged = [r for r in landed_rows if r[0] == "A013"]
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0][5], "A007")


class TestConnectRequiresEnv(unittest.TestCase):
    def test_missing_env_var_raises_configerror_before_any_network_call(self):
        old = os.environ.pop("CRM_DB_HOST")
        try:
            with self.assertRaises(ConfigError):
                crm._connect()
        finally:
            os.environ["CRM_DB_HOST"] = old


if __name__ == "__main__":
    unittest.main()

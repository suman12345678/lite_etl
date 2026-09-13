"""extract/billing -- billing.invoices + billing.subscriptions (REST, Stripe-like API).

    python -m extract.billing --mode daily    # land invoices AND subscriptions
    python -m extract.billing --mode hourly   # land-only: new invoices, no subscriptions,
                                               # no transform/publish (Schedule: hourly cadence)

Auth + host come only from BILLING_API_BASE_URL / BILLING_API_TOKEN (env vars, or a
secrets-manager reference injected as an env var by the orchestrator). Both sources
are incremental by `updated_at`: each run reads the last watermark from raw.*,
fetches everything with updated_at > watermark (cursor-paginated), lands it, then
advances the watermark to the max updated_at seen. Sources notes webhook retries
re-send the same invoice_id -- we do not dedupe here; append-only landing plus a
dedupe-on-latest-updated_at in dbt staging (stg_billing__invoices) is what makes
re-delivery safe.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any, Iterator

import requests

from extract.common import RawSink, get_watermark, require_env, retry_call, set_watermark

PAGE_LIMIT = 100

INVOICE_COLUMNS = [
    "invoice_id", "account_id", "plan_code", "invoice_date",
    "currency", "amount_local", "status", "updated_at",
]
SUBSCRIPTION_COLUMNS = [
    "subscription_id", "account_id", "plan_code", "start_date", "end_date", "canceled_at",
]


def _session() -> requests.Session:
    s = requests.Session()
    s.headers["Authorization"] = f"Bearer {require_env('BILLING_API_TOKEN')}"
    s.headers["Accept"] = "application/json"
    return s


class _RetryableHTTPError(Exception):
    """429 or 5xx -- worth retrying. Any other 4xx raises requests.HTTPError
    immediately (via resp.raise_for_status()), with no retry wasted on it."""


def _get(session: requests.Session, path: str, params: dict[str, Any]) -> dict:
    base = require_env("BILLING_API_BASE_URL").rstrip("/")

    def _do():
        resp = session.get(f"{base}{path}", params=params, timeout=30)
        if resp.status_code == 429:
            retry_after = float(resp.headers.get("Retry-After", "2"))
            raise _RetryableHTTPError(f"rate limited, retry after {retry_after}s")
        if resp.status_code >= 500:
            raise _RetryableHTTPError(f"server error {resp.status_code}")
        resp.raise_for_status()  # any other 4xx -> fail fast, not retried
        return resp.json()

    return retry_call(
        _do, max_attempts=5, base_delay_s=2.0,
        retry_on=(_RetryableHTTPError, requests.ConnectionError, requests.Timeout),
    )


def _paginate(session: requests.Session, path: str, since: str | None) -> Iterator[dict]:
    """Cursor pagination: {"data": [...], "has_more": bool, "next_cursor": str|None}."""
    cursor = None
    while True:
        params: dict[str, Any] = {"limit": PAGE_LIMIT}
        if since:
            params["updated_since"] = since
        if cursor:
            params["cursor"] = cursor
        page = _get(session, path, params)
        yield from page.get("data", [])
        if not page.get("has_more"):
            break
        cursor = page.get("next_cursor")
        if not cursor:
            break


def fetch_invoices(session: requests.Session, since: str | None) -> Iterator[dict]:
    yield from _paginate(session, "/v1/invoices", since)


def fetch_subscriptions(session: requests.Session, since: str | None) -> Iterator[dict]:
    yield from _paginate(session, "/v1/subscriptions", since)


def _invoice_row(raw: dict) -> tuple:
    return (
        raw["id"],
        raw["account_id"],
        raw["plan_code"],
        raw["invoice_date"],
        raw["currency"].upper(),
        float(raw["amount_local"]),
        raw["status"],
        raw["updated_at"],
    )


def _subscription_row(raw: dict) -> tuple:
    return (
        raw["id"],
        raw["account_id"],
        raw["plan_code"],
        raw["start_date"],
        raw.get("end_date"),
        raw.get("canceled_at"),
    )


def land_invoices(sink: RawSink, session: requests.Session) -> int:
    source = "billing.invoices"
    since = get_watermark(sink, source)
    rows, max_updated = [], since
    for raw in fetch_invoices(session, since):
        rows.append(_invoice_row(raw))
        if max_updated is None or raw["updated_at"] > max_updated:
            max_updated = raw["updated_at"]
    n = sink.append_rows("billing_invoices", INVOICE_COLUMNS, rows)
    if max_updated:
        set_watermark(sink, source, max_updated)
    return n


def land_subscriptions(sink: RawSink, session: requests.Session) -> int:
    source = "billing.subscriptions"
    since = get_watermark(sink, source)
    rows, max_updated = [], since
    for raw in fetch_subscriptions(session, since):
        rows.append(_subscription_row(raw))
        updated_at = raw.get("updated_at") or raw["start_date"]
        if max_updated is None or updated_at > max_updated:
            max_updated = updated_at
    n = sink.append_rows("billing_subscriptions", SUBSCRIPTION_COLUMNS, rows)
    if max_updated:
        set_watermark(sink, source, max_updated)
    return n


def run(mode: str) -> None:
    sink = RawSink()
    session = _session()
    try:
        n_inv = land_invoices(sink, session)
        print(f"landed {n_inv} billing.invoices row(s) (mode={mode})")
        if mode == "daily":
            n_sub = land_subscriptions(sink, session)
            print(f"landed {n_sub} billing.subscriptions row(s)")
        else:
            print("mode=hourly -> land-only, subscriptions/transform/publish skipped")
    finally:
        sink.close()


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=["daily", "hourly"], default="daily")
    args = ap.parse_args(argv)
    run(args.mode)
    return 0


if __name__ == "__main__":
    sys.exit(main())

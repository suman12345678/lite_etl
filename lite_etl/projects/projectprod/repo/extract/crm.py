"""extract/crm -- crm.accounts, a full daily snapshot from the CRM's Postgres
read replica.

    python -m extract.crm

Connection comes only from CRM_DB_HOST / CRM_DB_PORT / CRM_DB_NAME / CRM_DB_USER /
CRM_DB_PASSWORD (env vars; in prod CRM_DB_PASSWORD is injected by the orchestrator
from Secrets Manager -- never a literal here). Sources notes this table carries PII
(`billing_email`, `company_name`) and merged-account pointers (`merged_into`); both
are landed as-is -- PII hashing and merge resolution happen at the staging boundary
(dbt: stg_crm__accounts), never here.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from typing import Iterator

import psycopg2

from extract.common import RawSink, require_env, retry_call

ACCOUNT_COLUMNS = [
    "account_id", "company_name", "billing_email", "country",
    "company_domain", "merged_into", "loaded_at",
]

_SNAPSHOT_QUERY = """
    select account_id, company_name, billing_email, country, company_domain, merged_into
    from accounts
"""


def _connect():
    def _do():
        return psycopg2.connect(
            host=require_env("CRM_DB_HOST"),
            port=int(require_env("CRM_DB_PORT")),
            dbname=require_env("CRM_DB_NAME"),
            user=require_env("CRM_DB_USER"),
            password=require_env("CRM_DB_PASSWORD"),
            sslmode="require",
            connect_timeout=10,
        )

    return retry_call(_do, max_attempts=3, base_delay_s=3.0, retry_on=(psycopg2.OperationalError,))


def fetch_accounts(conn) -> Iterator[tuple]:
    with conn.cursor() as cur:
        cur.execute(_SNAPSHOT_QUERY)
        for row in cur:
            yield row


def land_accounts(sink: RawSink, conn) -> int:
    loaded_at = datetime.now(timezone.utc).isoformat()
    rows = [tuple(r) + (loaded_at,) for r in fetch_accounts(conn)]
    return sink.replace_rows("crm_accounts", ACCOUNT_COLUMNS, rows)


def run() -> None:
    sink = RawSink()
    conn = _connect()
    try:
        n = land_accounts(sink, conn)
        print(f"landed {n} crm.accounts row(s) (full snapshot)")
    finally:
        conn.close()
        sink.close()


def main(argv: list[str] | None = None) -> int:
    run()
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Shared helpers for extract/billing.py, extract/crm.py, extract/ref.py:
env-var config, HTTP retry with backoff, and the raw-table sink that lands rows
into whichever warehouse engine is selected by the ENGINE environment variable.

Every credential / connection value in this file (and in every extract/*.py module)
comes from os.environ, or in prod from a secrets-manager-backed env var injected by
the orchestrator (see ../orchestration/). Nothing here is ever a literal host,
account id, or token.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Iterable, Sequence

logger = logging.getLogger("extract")
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))


class ConfigError(RuntimeError):
    """Raised when a required environment variable is missing."""


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ConfigError(
            f"missing required environment variable {name!r} -- set it directly, or point "
            "the orchestrator's secrets injection at it, before running this extractor"
        )
    return value


def env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name, default)


def retry_call(fn, *, max_attempts: int = 5, base_delay_s: float = 1.0, retry_on=(Exception,)):
    """Exponential-backoff retry. `fn` takes no arguments; call it, retry on failure."""
    attempt = 0
    while True:
        try:
            return fn()
        except retry_on as exc:
            attempt += 1
            if attempt >= max_attempts:
                raise
            delay = base_delay_s * (2 ** (attempt - 1))
            logger.warning("attempt %d/%d failed (%s); retrying in %.1fs", attempt, max_attempts, exc, delay)
            time.sleep(delay)


def connect(engine: str | None = None, *, database: str | None = None, schema: str | None = None):
    """Open a raw DB-API connection to the given engine (duckdb | databricks |
    snowflake), defaulted to the given database/schema so unqualified table
    names -- as rules.yml's SQL uses -- resolve correctly without string
    surgery. RawSink (below) is the raw-landing-specific wrapper extract/*.py
    uses; publish/gate.py calls this directly against the marts schema dbt
    just built.

    ENGINE=duckdb (default, local/CI)  -> file path from DUCKDB_PATH
    ENGINE=databricks                  -> DATABRICKS_HOST / _HTTP_PATH / _TOKEN
    ENGINE=snowflake                   -> SNOWFLAKE_ACCOUNT / _USER / _PASSWORD /
                                           _WAREHOUSE / _DATABASE / _SCHEMA / _ROLE
    """
    engine = (engine or env("ENGINE", "duckdb") or "duckdb").lower()
    if engine == "duckdb":
        import duckdb  # local import: not a hard dependency for databricks/snowflake runs

        con = duckdb.connect(env("DUCKDB_PATH", "target/raw.duckdb"))
        if schema:
            con.execute(f"create schema if not exists {schema}")
            con.execute(f"set schema = '{schema}'")
        return con
    if engine == "databricks":
        from databricks import sql as databricks_sql

        return databricks_sql.connect(
            server_hostname=require_env("DATABRICKS_HOST"),
            http_path=require_env("DATABRICKS_HTTP_PATH"),
            access_token=require_env("DATABRICKS_TOKEN"),
            catalog=database or env("DBT_CATALOG"),
            schema=schema or env("DBT_SCHEMA", "marts"),
        )
    if engine == "snowflake":
        import snowflake.connector

        return snowflake.connector.connect(
            account=require_env("SNOWFLAKE_ACCOUNT"),
            user=require_env("SNOWFLAKE_USER"),
            password=require_env("SNOWFLAKE_PASSWORD"),
            warehouse=require_env("SNOWFLAKE_WAREHOUSE"),
            database=database or require_env("SNOWFLAKE_DATABASE"),
            schema=schema or env("SNOWFLAKE_SCHEMA", "MARTS"),
            role=env("SNOWFLAKE_ROLE"),
        )
    raise ConfigError(f"unknown ENGINE={engine!r} -- expected duckdb, databricks, or snowflake")


class RawSink:
    """Writes extracted rows into raw.<table> of the engine named by ENGINE.
    Thin wrapper around connect(..., schema='raw') plus insert/watermark helpers.
    """

    def __init__(self, engine: str | None = None):
        self.engine = (engine or env("ENGINE", "duckdb") or "duckdb").lower()
        self._placeholder = "?" if self.engine == "duckdb" else "%s"
        self._con = connect(self.engine, schema="raw")

    def _cursor(self):
        return self._con.cursor() if hasattr(self._con, "cursor") else self._con

    def ensure_table(self, table: str, ddl_columns: str) -> None:
        self._cursor().execute(f"create table if not exists raw.{table} ({ddl_columns})")

    def replace_rows(self, table: str, columns: Sequence[str], rows: Iterable[Sequence[Any]]) -> int:
        """Full-snapshot load: truncate then insert. Used by extract/crm, extract/ref."""
        rows = list(rows)
        self._cursor().execute(f"delete from raw.{table}")
        self._insert_many(table, columns, rows)
        self.commit()
        return len(rows)

    def append_rows(self, table: str, columns: Sequence[str], rows: Iterable[Sequence[Any]]) -> int:
        """Incremental load: append. Dedup on latest updated_at happens downstream in
        dbt staging (stg_billing__invoices), which is where Sources' webhook-retry
        quirk is actually handled -- landing stays append-only and idempotent-safe."""
        rows = list(rows)
        self._insert_many(table, columns, rows)
        self.commit()
        return len(rows)

    def _insert_many(self, table: str, columns: Sequence[str], rows: list[Sequence[Any]]) -> None:
        if not rows:
            return
        placeholders = ", ".join([self._placeholder] * len(columns))
        collist = ", ".join(columns)
        sql = f"insert into raw.{table} ({collist}) values ({placeholders})"
        cur = self._cursor()
        for row in rows:
            cur.execute(sql, row)

    def commit(self) -> None:
        if hasattr(self._con, "commit"):
            self._con.commit()

    def close(self) -> None:
        self._con.close()


# ---- watermark bookkeeping (incremental-by-updated_at sources) ----------------

_WATERMARK_TABLE = "_extract_watermarks"


def get_watermark(sink: RawSink, source: str) -> str | None:
    sink.ensure_table(_WATERMARK_TABLE, "source_name varchar, last_updated_at varchar")
    cur = sink._cursor()
    cur.execute(
        f"select last_updated_at from raw.{_WATERMARK_TABLE} where source_name = {sink._placeholder}",
        (source,),
    )
    row = cur.fetchone()
    return row[0] if row else None


def set_watermark(sink: RawSink, source: str, value: str) -> None:
    sink.ensure_table(_WATERMARK_TABLE, "source_name varchar, last_updated_at varchar")
    cur = sink._cursor()
    ph = sink._placeholder
    cur.execute(f"delete from raw.{_WATERMARK_TABLE} where source_name = {ph}", (source,))
    cur.execute(
        f"insert into raw.{_WATERMARK_TABLE} (source_name, last_updated_at) values ({ph}, {ph})",
        (source, value),
    )
    sink.commit()

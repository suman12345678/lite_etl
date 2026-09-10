"""Landing writer: atomic Delta append + manifest + POS supersede. Buildsheet: component-buildsheet-landing.md

Stub - Phase 3 scaffold. Implement against the matching buildsheet.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import date


class LandingSchemaError(Exception):
    ...


@dataclass
class LandResult:
    landed_rows: int
    table: str
    delta_version: int


def write_bronze(result, *, source: str, object: str, business_date: date,
                 run_id: str, settings) -> LandResult:
    """Atomic append to bronze.<source>__<object> with _run_id/_source_file/_extracted_at/_ingest_date."""
    raise NotImplementedError  # TODO temp-write then single Delta commit


def supersede_prior(source: str = "pos", *, business_date: date, store: str,
                    new_etag: str, settings) -> int:
    """Set _superseded = true on rows for (business_date, store) with a different _file_etag. Never delete."""
    raise NotImplementedError  # TODO


def write_manifest(manifest, settings) -> str:
    raise NotImplementedError  # TODO write last, after a successful commit


"""Local CSV connector - the one connector that ships enabled."""
from __future__ import annotations

import csv

from .base import Extractor


class CsvExtractor(Extractor):
    type_name = "csv"

    def extract(self) -> list[dict]:
        conn = self.source.connection
        path = self.source.resolve_path(conn["path"])
        if not path.exists():
            raise FileNotFoundError(f"CSV not found for '{self.source.name}': {path}")

        delimiter = conn.get("delimiter", ",")
        encoding = conn.get("encoding", "utf-8")
        with path.open("r", newline="", encoding=encoding) as fh:
            reader = csv.DictReader(fh, delimiter=delimiter)
            return [dict(row) for row in reader]
